import { readFile, mkdir, rename, readdir } from 'node:fs/promises';
import { join, basename } from 'node:path';
import { Sequelize, DataTypes, Model } from 'sequelize';

// 2. Initialize Sequelize with the 'raw' schema
const sequelize = new Sequelize('prosperous_universe', 'postgres', 'abc123', {
  host: 'localhost',
  dialect: 'postgres',
  logging: false,
  schema: 'raw',
});

// 3. Define the Building Model
class Building extends Model {
  declare id: string;
  declare ticker: string;
  declare name: string;
  declare areaCost: number;
  declare submittedBy: string;
}

Building.init(
  {
    id: {
      type: DataTypes.STRING,
      primaryKey: true,
    },
    ticker: {
      type: DataTypes.STRING,
      allowNull: true, // Made flexible to prevent validation errors if missing
    },
    name: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    areaCost: {
      type: DataTypes.INTEGER,
      field: 'area_cost',
      allowNull: true,
    },
    submittedBy: {
      type: DataTypes.STRING,
      field: 'user_name_submitted',
      allowNull: true,
    },
  },
  {
    sequelize,
    modelName: 'Building',
    tableName: 'buildings',
    schema: 'raw'
  }
);

// 4. Define the BuildingCost Model
class BuildingCost extends Model {
  declare id: number;
  declare commodityName: string;
  declare commodityTicker: string;
  declare weight: number;
  declare volume: number;
  declare amount: number;
  declare buildingId: string;
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
      allowNull: true,
      field: 'commodity_name',
    },
    commodityTicker: {
      type: DataTypes.STRING,
      allowNull: true,
      field: 'commodity_ticker',
    },
    weight: DataTypes.FLOAT,
    volume: DataTypes.FLOAT,
    amount: {
      type: DataTypes.INTEGER,
      allowNull: true,
    },
  },
  {
    sequelize,
    modelName: 'BuildingCost',
    tableName: 'building_costs',
    schema: 'raw'
  }
);

// 5. Define Relational Associations
Building.hasMany(BuildingCost, {
  foreignKey: 'buildingId',
  as: 'buildingCosts',
  onDelete: 'CASCADE',
});
BuildingCost.belongsTo(Building, {
  foreignKey: 'buildingId',
});

// 6. Data Seeding Function with Transaction Handling
async function seedData(dataPayload: any) {
  const buildingId = dataPayload.BuildingId;
  
  if (!buildingId) {
    throw new Error('Missing "BuildingId" in JSON payload.');
  }

  const buildingData = {
    id: buildingId,
    ticker: dataPayload.Ticker || null,
    name: dataPayload.Name || null,
    areaCost: dataPayload.AreaCost ?? null,
    submittedBy: dataPayload.UserNameSubmitted || null,
  };

  const buildingCostsData = (dataPayload.BuildingCosts || []).map((cost: any) => ({
    commodityName: cost.CommodityName || null,
    commodityTicker: cost.CommodityTicker || null,
    weight: cost.Weight ?? null,
    volume: cost.Volume ?? null,
    amount: cost.Amount ?? null,
    buildingId: buildingId,
  }));

  // Use a transaction to safely handle existing data updates
  const t = await sequelize.transaction();

  try {
    // Upsert the main building record
    await Building.upsert(buildingData, { transaction: t });

    // Clear old dependent costs for this building to prevent duplicates/conflicts
    await BuildingCost.destroy({ where: { buildingId }, transaction: t });

    // Insert new costs if any exist
    if (buildingCostsData.length > 0) {
      await BuildingCost.bulkCreate(buildingCostsData, { transaction: t });
    }

    await t.commit();
    console.log(`\nSUCCESS: Upserted Building "${buildingData.name || buildingId}" into schema "raw".\n`);
  } catch (error) {
    await t.rollback();
    throw error;
  }
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

async function readJson(filePath: any) {
  try {
    const data = await readFile(filePath, 'utf-8');
    const json = JSON.parse(data);

    console.log(`Loaded JSON successfully from ${basename(filePath)}!`);
    return json;
  } catch (error: any) {
    console.error(`Failed to read or parse JSON file ${basename(filePath)}:`, error.message);
  }
}

// 8. Main Execution Wrapper
async function main() {
  const inputFolder = process.argv[2] || '/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed';
  const processedFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed';

  try {
    await sequelize.authenticate();
    console.log('PostgreSQL connection established successfully.');

    await sequelize.createSchema('raw', {}).catch(() => {});
    await sequelize.sync({ force: false });

    const files = await readdir(inputFolder);
    const targetFiles = files.filter(file => file.endsWith('.json') && !file.endsWith('AI1.json'));

    if (targetFiles.length === 0) {
      console.log('No eligible files (not ending with AI1.json) found in the directory.');
      return;
    }

    for (const file of targetFiles) {
      const jsonFilePath = join(inputFolder, file);

      let data = await readJson(jsonFilePath);
      if (!data) continue;

      try {
        await seedData(data);

        if (data.BuildingId) {
          await getBuilding(data.BuildingId);
        }

        const processedFilePath = join(processedFolder, file);
        await mkdir(processedFolder, { recursive: true });
        await rename(jsonFilePath, processedFilePath);
        console.log(`Successfully moved JSON file to: ${processedFilePath}`);
      } catch (error: any) {
        console.error(`Error processing file ${file}:`, error.message);
        if (error.errors && Array.isArray(error.errors)) {
          error.errors.forEach((err: any) => {
            console.error(`   -> Validation Detail [${err.path}]: ${err.message}`);
          });
        }
      }
    }
  } catch (error) {
    console.error('Database Operation Failed:', error);
  } finally {
    await sequelize.close();
  }
}

main();