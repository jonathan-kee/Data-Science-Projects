import { readFile, writeFile, mkdir, rename } from 'node:fs/promises';
import { join, basename } from 'node:path';
import axios from "axios";

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

function LambdaCreateTable(data: any, tablename: string) {
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

    let createTable = `CREATE TABLE IF NOT EXISTS raw.` + tablename + `_raw\n(\n`
    for (let i = 0; i < arrayOfTuple.length; i++) {
        let lengthOfTuple = arrayOfTuple[i].length
        createTable += '"' + arrayOfTuple[i][0] + '"      ' + arrayOfTuple[i][1] + ',\n'
    }
    createTable = createTable.slice(0, -2) + '\n);';
    return createTable;
}

function LambdaInsertTable(data: any, tablename: string) {
    const lengthOfData = data.length
    // 1. Initialize string with TRUNCATE TABLE statement
    let insert = `TRUNCATE TABLE raw.${tablename}_raw;\n\n`;

    for (let i = 0; i < lengthOfData; i++) {
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

        if (i == 0) {
            let insertParenthesis = "("
            for (let i = 0; i < arrayOfTuple.length; i++) {
                insertParenthesis += '"' + arrayOfTuple[i][0] + '"' + ","
            }
            insertParenthesis = insertParenthesis.slice(0, -1) + ")\nVALUES "

            insert += `INSERT INTO raw.${tablename}_raw ` + insertParenthesis
        }

        insert += "("
        for (let i = 0; i < arrayOfTuple.length; i++) {
            if (typeof arrayOfTuple[i][2] == 'string') {
                insert += `'${arrayOfTuple[i][2]}'`;
            } else if (typeof arrayOfTuple[i][2] == 'number') {
                insert += `${arrayOfTuple[i][2]}`;
            }
            insert += ","
        }
        insert = insert.slice(0, -1) + "),\n"
    }
    insert = insert.slice(0, -2) + ';';
    return insert;
}

async function main() {
    const urlString = process.argv[2]; // "https://rest.fnar.net/exchange/cxpc/ALO.AI1"
    const url = new URL(urlString);
    // pathname will be: "/exchange/cxpc/AL.AI1"
    const segments = url.pathname.split('/');
    const lastSegment = segments[segments.length - 1]; // "AL.AI1"
    const [part1, part2] = lastSegment.split('.');
    let fileNameGeneric: string = "cxpc_" + part1 + "_" + part2;

    const response = await axios.get(urlString, {
        headers: {
            'accept': 'application/json'
        },
        timeout: 15000, // 15 seconds
    });
    let stringData = JSON.stringify(response.data, null, 2);

    const jsonFilePath = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed/' + getTodayDateFileName(fileNameGeneric, ".json");

    // null 2 is to format the json properly
    await writeFile(jsonFilePath, stringData, 'utf-8');

    // Read file on disk
    let data = await readJsonArray(jsonFilePath);
    if (!data) return;

    let createTable: string = LambdaCreateTable(data, fileNameGeneric);
    let insertTable: string = LambdaInsertTable(data, fileNameGeneric);

    let fullsql = createTable + "\n\n" + insertTable;
    console.log(fullsql);

    // --- Output section ---
    const outputFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sql';
    const outputPath = join(outputFolder, getTodayDateFileName(fileNameGeneric, ".sql"));

    // --- Processed JSON target directory ---
    const processedFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed';
    const processedFilePath = join(processedFolder, basename(jsonFilePath));

    try {
        // 1. Ensure the SQL output folder exists and write the SQL file
        await mkdir(outputFolder, { recursive: true });
        await writeFile(outputPath, fullsql, 'utf-8');
        console.log(`Successfully saved SQL file to: ${outputPath}`);

        // 2. Ensure the processed folder exists and move the JSON file
        await mkdir(processedFolder, { recursive: true });
        await rename(jsonFilePath, processedFilePath);
        console.log(`Successfully moved JSON file to: ${processedFilePath}`);
    } catch (error: any) {
        console.error('Error during output or file moving step:', error.message);
    }
}

main();