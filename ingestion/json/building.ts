let data = {
    "BuildingCosts": [
        {
            "CommodityName": "basicBulkhead",
            "CommodityTicker": "BBH",
            "Weight": 0.5,
            "Volume": 0.800000011920929,
            "Amount": 2
        },
        {
            "CommodityName": "basicDeckElements",
            "CommodityTicker": "BDE",
            "Weight": 0.10000000149011612,
            "Volume": 1.5,
            "Amount": 2
        },
        {
            "CommodityName": "basicStructuralElements",
            "CommodityTicker": "BSE",
            "Weight": 0.30000001192092896,
            "Volume": 0.5,
            "Amount": 2
        },
        {
            "CommodityName": "basicWindow",
            "CommodityTicker": "BTA",
            "Weight": 0.30000001192092896,
            "Volume": 0.4000000059604645,
            "Amount": 2
        },
        {
            "CommodityName": "truss",
            "CommodityTicker": "TRU",
            "Weight": 0.10000000149011612,
            "Volume": 1.5,
            "Amount": 2
        }
    ],
    "Recipes": [],
    "BuildingId": "79f8f9bf4a56c464041c18995b00c16e",
    "Name": "habitationSettler",
    "Ticker": "HB2",
    "Expertise": null,
    "Pioneers": 0,
    "Settlers": 0,
    "Technicians": 0,
    "Engineers": 0,
    "Scientists": 0,
    "AreaCost": 12,
    "UserNameSubmitted": "TAIYI",
    "Timestamp": "2026-07-29T12:58:38.274573Z"
}

class BuildingCosts {
    commodityName: string
    commodityTicker: string
    amount: number

    constructor(commodityName: string, commodityTicker: string, amount: number) {
        this.commodityName = commodityName;
        this.commodityTicker = commodityTicker;
        this.amount = amount;
    }
}

class Building {
    ticker: string
    name: string
    arrayOfBuildingCosts: BuildingCosts[]

    constructor(ticker: string, name: string, arrayOfBuildingCosts: BuildingCosts[]) {
        this.ticker = ticker;
        this.name = name;
        this.arrayOfBuildingCosts = arrayOfBuildingCosts;
    }

}

let arrayOfBuildingCosts = []
for (let i = 0; i < data.BuildingCosts.length; i++) {
    let buidlingCosts = new BuildingCosts(
        data.BuildingCosts[i].CommodityName,
        data.BuildingCosts[i].CommodityTicker,
        data.BuildingCosts[i].Amount
    )
    arrayOfBuildingCosts.push(buidlingCosts)
}

let building = new Building(data.Ticker, data.Name, arrayOfBuildingCosts);


