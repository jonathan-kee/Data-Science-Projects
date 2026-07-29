import { readFile } from 'node:fs/promises';

async function readJsonArray(filePath: any) {
    try {
        const data = await readFile(filePath, 'utf-8');
        const jsonArray = JSON.parse(data);

        if (!Array.isArray(jsonArray)) {
            throw new Error('The JSON file does not contain a top-level array.');
        }

        console.log(`Loaded ${jsonArray.length} items successfully!`);
        return jsonArray;
    } catch (error: any) {
        console.error('Failed to read or parse JSON file:', error.message);
    }
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

function LambdaCreateTable(data: any, tablename:string = "cxpc_al_ai1_raw") {
    const columns: string[] = Object.keys(data[0])
    const rowValues = Object.values(data[0]);
    let tuple: [string, string, any];
    let arrayOfTuple: [string, string, any][] = [];

    for (let i = 0; i < columns.length; i++) {
        if (typeof rowValues[i] == 'string') {
            tuple = [columns[i], "varchar(20)", rowValues[i]]
        } else if (typeof rowValues[i] == 'number') {
            tuple = [columns[i], "numeric(15, 2)", rowValues[i]]
        } else {
            tuple = [columns[i], "varchar(20)", rowValues[i]]
        }
        arrayOfTuple.push(tuple);
    }

    let createTable = `create table if not exists `+ tablename +`_raw\n(\n`
    for (let i = 0; i < arrayOfTuple.length; i++) {
        let lengthOfTuple = arrayOfTuple[i].length
        createTable += '"'+ arrayOfTuple[i][0] + '"      ' + arrayOfTuple[i][1] + ',\n'
    }
    createTable = createTable.slice(0, -2) + '\n);';
    console.log(createTable)

     // 1. Initialize string with TRUNCATE TABLE statement
  let insert = `TRUNCATE TABLE ${tablename};\n\n`;

  let insertParenthesis = "("
  for (let i = 0; i < arrayOfTuple.length; i++) {
    insertParenthesis += '"'+arrayOfTuple[i][0] + '"' + ","
  }
  insertParenthesis = insertParenthesis.slice(0, -1) + ")\nVALUES "

  insert += `INSERT INTO ${tablename} ` + insertParenthesis
  

  insert += "("
  for (let i = 0; i < arrayOfTuple.length; i++) {
    if(typeof arrayOfTuple[i][2] == 'string') {
        insert += `'${arrayOfTuple[i][2]}'`;
    } else if (typeof arrayOfTuple[i][2] == 'number'){
        insert += `${arrayOfTuple[i][2]}`;
    }
    insert+= ","
  }
  insert = insert.slice(0, -1) + "),"


  console.log(insert)

  console.log(arrayOfTuple)
}

function LambdaInsertTable(data: any, tablename:string = "cxpc_al_ai1_raw") {
    const lengthOfData = data.length
    // 1. Initialize string with TRUNCATE TABLE statement
    let insert = `TRUNCATE TABLE ${tablename};\n\n`;

    for (let i = 0; i < lengthOfData - 2900; i++){
        const columns: string[] = Object.keys(data[i])
        const rowValues = Object.values(data[i]);
        let tuple: [string, string, any];
        let arrayOfTuple: [string, string, any][] = [];

        for (let j = 0; j < columns.length; j++) {
            if (typeof rowValues[j] == 'string') {
                tuple = [columns[j], "varchar(20)", rowValues[j]]
            } else if (typeof rowValues[j] == 'number') {
                tuple = [columns[j], "numeric(15, 2)", rowValues[j]]
            } else {
                tuple = [columns[j], "varchar(20)", rowValues[j]]
            }
            arrayOfTuple.push(tuple);
        }

        if(i==0) {
            let insertParenthesis = "("
            for (let i = 0; i < arrayOfTuple.length; i++) {
                insertParenthesis += '"'+arrayOfTuple[i][0] + '"' + ","
            }
            insertParenthesis = insertParenthesis.slice(0, -1) + ")\nVALUES "

            insert += `INSERT INTO ${tablename} ` + insertParenthesis
        }
        
        insert += "("
        for (let i = 0; i < arrayOfTuple.length; i++) {
            if(typeof arrayOfTuple[i][2] == 'string') {
                insert += `'${arrayOfTuple[i][2]}'`;
            } else if (typeof arrayOfTuple[i][2] == 'number'){
                insert += `${arrayOfTuple[i][2]}`;
            }
            insert+= ","
        }
        insert = insert.slice(0, -1) + "),\n"
    }
    insert = insert.slice(0, -2) + ';';
    console.log(insert);
}

async function main() {

    // label the data that can be generic
    // generic variables
    let apiGeneric: string = "https://rest.fnar.net/exchange/cxpc/AL.AI1";
    let fileNameGeneric: string = "cxpc_AL_AI1";
    let tableNameGeneric: string = "raw.cxpc_AL_AI1_raw";
    let columnGeneric: string[] = ["Interval", "DateEpochMs", "Open", "Close", "High", "Low", "Volume", "Traded"]
    let lambdaToProcessTheArray;

    const jsonFilePath = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed/' + getTodayDateFileName(fileNameGeneric, ".json");

    // Read file on disk
    let data = await readJsonArray(jsonFilePath,);
    if (!data) return;

    // LambdaCreateTable(data, fileNameGeneric);
    LambdaInsertTable(data, fileNameGeneric)
}

main();