import { Sequelize, DataTypes, Model } from 'sequelize';

// 1. Data Payload
const data = {
  BuildingCosts: [
    {
      CommodityName: 'basicBulkhead',
      CommodityTicker: 'BBH',
      Weight: 0.5,
      Volume: 0.800000011920929,
      Amount: 2,
    },
    {
      CommodityName: 'basicDeckElements',
      CommodityTicker: 'BDE',
      Weight: 0.10000000149011612,
      Volume: 1.5,
      Amount: 2,
    },
    {
      CommodityName: 'basicStructuralElements',
      CommodityTicker: 'BSE',
      Weight: 0.30000001192092896,
      Volume: 0.5,
      Amount: 2,
    },
    {
      CommodityName: 'basicWindow',
      CommodityTicker: 'BTA',
      Weight: 0.30000001192092896,
      Volume: 0.4000000059604645,
      Amount: 2,
    },
    {
      CommodityName: 'truss',
      CommodityTicker: 'TRU',
      Weight: 0.10000000149011612,
      Volume: 1.5,
      Amount: 2,
    },
  ],
  Recipes: [],
  BuildingId: '79f8f9bf4a56c464041c18995b00c16e',
  Name: 'habitationSettler',
  Ticker: 'HB2',
  Expertise: null,
  Pioneers: 0,
  Settlers: 0,
  Technicians: 0,
  Engineers: 0,
  Scientists: 0,
  AreaCost: 12,
  UserNameSubmitted: 'TAIYI',
  Timestamp: '2026-07-29T12:58:38.274573Z',
};

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
async function seedData(dataPayload: typeof data) {
  // Ensure the "raw" schema exists in PostgreSQL before syncing
  await sequelize.createSchema('raw', {});

  // force: true drops existing tables in raw schema and recreates raw.buildings & raw.building_costs
  await sequelize.sync({ force: true });

  const newBuilding = await Building.create(
    {
      id: dataPayload.BuildingId,
      ticker: dataPayload.Ticker,
      name: dataPayload.Name,
      areaCost: dataPayload.AreaCost,
      submittedBy: dataPayload.UserNameSubmitted,
      buildingCosts: dataPayload.BuildingCosts.map((cost) => ({
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

// 8. Main Execution Wrapper
async function main() {
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
}

main();