import { readFile, writeFile, mkdir, rename } from 'node:fs/promises';
import { join, basename } from 'node:path';
import { Sequelize, DataTypes, Model } from 'sequelize';
import axios from "axios";

// 2. Initialize Sequelize with the 'raw' schema
const sequelize = new Sequelize('prosperous_universe', 'postgres', 'abc123', {
  host: 'localhost',
  dialect: 'postgres',
  logging: console.log,
  schema: 'raw', // Sets global search path to the "raw" schema
});

// 3. Define the Building Model
class Building extends Model {
  public id!: string;
  public ticker!: string;
  public name!: string;
  public areaCost!: number;
  public submittedBy!: string;
}

Building.init(
  {
    id: {
      type: DataTypes.STRING,
      primaryKey: true,
    },
    ticker: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    name: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    areaCost: {
      type: DataTypes.INTEGER,
      field: 'area_cost',
    },
    submittedBy: {
      type: DataTypes.STRING,
      field: 'user_name_submitted',
    },
  },
  {
    sequelize,
    modelName: 'Building',
    tableName: 'buildings',
    schema: 'raw' // Target table: raw.buildings
  }
);

// 4. Define the BuildingCost Model
class BuildingCost extends Model {
  public id!: number;
  public commodityName!: string;
  public commodityTicker!: string;
  public weight!: number;
  public volume!: number;
  public amount!: number;
  public buildingId!: string;
}

BuildingCost.init(
  {
    id: {
      type: DataTypes.INTEGER,
      autoIncrement: true,
      primaryKey: true,
    },
    commodityName: {
      type: DataTypes.STRING,
      allowNull: false,
      field: 'commodity_name',
    },
    commodityTicker: {
      type: DataTypes.STRING,
      allowNull: false,
      field: 'commodity_ticker',
    },
    weight: DataTypes.FLOAT,
    volume: DataTypes.FLOAT,
    amount: {
      type: DataTypes.INTEGER,
      allowNull: false,
    },
  },
  {
    sequelize,
    modelName: 'BuildingCost',
    tableName: 'building_costs',
    schema: 'raw' // Target table: raw.building_costs
  }
);

// 5. Define Relational Associations
Building.hasMany(BuildingCost, {
  foreignKey: 'buildingId',
  as: 'buildingCosts',
});
BuildingCost.belongsTo(Building, {
  foreignKey: 'buildingId',
});

// 6. Data Seeding Function
async function seedData(dataPayload: any) {
  // Ensure the "raw" schema exists in PostgreSQL before syncing
  await sequelize.createSchema('raw', {});

  // force: true drops existing tables in raw schema and recreates raw.buildings & raw.building_costs
  await sequelize.sync({ force: false });

  const newBuilding = await Building.create(
    {
      id: dataPayload.BuildingId,
      ticker: dataPayload.Ticker,
      name: dataPayload.Name,
      areaCost: dataPayload.AreaCost,
      submittedBy: dataPayload.UserNameSubmitted,
      buildingCosts: dataPayload.BuildingCosts.map((cost: any) => ({
        commodityName: cost.CommodityName,
        commodityTicker: cost.CommodityTicker,
        weight: cost.Weight,
        volume: cost.Volume,
        amount: cost.Amount,
      })),
    },
    {
      include: [{ model: BuildingCost, as: 'buildingCosts' }],
    }
  );

  console.log(`\nSUCCESS: Saved Building "${newBuilding.name}" (${newBuilding.id}) to schema "raw".\n`);
}

// 7. Query Function
async function getBuilding(buildingId: string) {
  const result = await Building.findByPk(buildingId, {
    include: [
      {
        model: BuildingCost,
        as: 'buildingCosts',
      },
    ],
  });

  console.log('--- Queried Database Result (from schema "raw") ---');
  console.log(JSON.stringify(result, null, 2));
}

function getTodayDateFileName(filename: any, extension: any) {
  const today = new Date();

  const day = String(today.getDate()).padStart(2, '0');
  const month = String(today.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
  const year = today.getFullYear();

  const ddMMyyyy = `${day}${month}${year}`;
  console.log(ddMMyyyy); // Output: "29072026

  return filename + "_" + ddMMyyyy + extension;
}

async function readJson(filePath: any) {
  try {
    const data = await readFile(filePath, 'utf-8');
    const json = JSON.parse(data);

    console.log(`Loaded ${json.length} items successfully!`);
    return json;
  } catch (error: any) {
    console.error('Failed to read or parse JSON file:', error.message);
  }
}

// 8. Main Execution Wrapper
async function main() {
  const urlString = process.argv[2]; // "https://rest.fnar.net/building/HB2";
  const url = new URL(urlString);
  const segments = url.pathname.split('/');
  const lastSegment = segments[segments.length - 1]; // "HB2"
  let fileNameGeneric: string = "building_" + lastSegment;

  const response = await axios.get(urlString, {
    headers: {
      'accept': 'application/json'
    },
    timeout: 10000, // 10 seconds
  });

  let stringData = JSON.stringify(response.data, null, 2);

  const jsonFilePath = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed/' + getTodayDateFileName(fileNameGeneric, ".json");

  // null 2 is to format the json properly
  await writeFile(jsonFilePath, stringData, 'utf-8');

  // Read file on disk
  let data = await readJson(jsonFilePath);
  if (!data) return;

  try {
    // Authenticate PostgreSQL connection
    await sequelize.authenticate();
    console.log('PostgreSQL connection established successfully.');

    // Create schema, sync models, and insert data
    await seedData(data);

    // Fetch and log data back from the DB
    await getBuilding(data.BuildingId);
  } catch (error) {
    console.error('Database Operation Failed:', error);
  } finally {
    // Gracefully terminate connection
    await sequelize.close();
  }

  // --- Processed JSON target directory ---
  const processedFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed';
  const processedFilePath = join(processedFolder, basename(jsonFilePath));

  try {
    // 2. Ensure the processed folder exists and move the JSON file
    await mkdir(processedFolder, { recursive: true });
    await rename(jsonFilePath, processedFilePath);
    console.log(`Successfully moved JSON file to: ${processedFilePath}`);
  } catch (error: any) {
    console.error('Error during output or file moving step:', error.message);
  }
}

main();