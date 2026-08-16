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
    console.log(ddMMyyyy);

    return filename + "_" + ddMMyyyy + extension;
}

function getFormattedDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function LambdaCreateTable(data: any, tablename: string) {
    const columns: string[] = Object.keys(data[0])
    const rowValues = Object.values(data[0]);
    let arrayOfTuple: [string, string][] = [];

    for (let i = 0; i < columns.length; i++) {
        if (typeof rowValues[i] == 'string') {
            arrayOfTuple.push([columns[i], "varchar(20)"]);
        } else if (typeof rowValues[i] == 'number') {
            arrayOfTuple.push([columns[i], "numeric(15, 2)"]);
        } else {
            arrayOfTuple.push([columns[i], "varchar(20)"]);
        }
    }
    // Include file_date column definition
    arrayOfTuple.push(["file_date", "date"]);

    let createTable = `CREATE TABLE IF NOT EXISTS raw.` + tablename + `_raw\n(\n`;
    for (let i = 0; i < arrayOfTuple.length; i++) {
        createTable += `    "` + arrayOfTuple[i][0] + `"      ` + arrayOfTuple[i][1] + `,\n`;
    }
    createTable += `    CONSTRAINT pk_${tablename}_raw PRIMARY KEY ("Interval", "DateEpochMs")\n`;
    createTable += `);`;
    return createTable;
}

function LambdaInsertTable(data: any, tablename: string) {
    const lengthOfData = data.length;
    let insert = "";
    const fileDateValue = getFormattedDate();

    for (let i = 0; i < lengthOfData; i++) {
        const columns: string[] = Object.keys(data[i]);
        const rowValues = Object.values(data[i]);
        let arrayOfTuple: [string, any][] = [];

        for (let j = 0; j < columns.length; j++) {
            arrayOfTuple.push([columns[j], rowValues[j]]);
        }
        // Include file_date value for each row
        arrayOfTuple.push(["file_date", fileDateValue]);

        if (i == 0) {
            let insertParenthesis = "(";
            for (let k = 0; k < arrayOfTuple.length; k++) {
                insertParenthesis += '"' + arrayOfTuple[k][0] + '"' + ",";
            }
            insertParenthesis = insertParenthesis.slice(0, -1) + ")\nVALUES ";

            insert += `INSERT INTO raw.${tablename}_raw ` + insertParenthesis;
        }

        insert += "(";
        for (let k = 0; k < arrayOfTuple.length; k++) {
            const colName = arrayOfTuple[k][0];
            const val = arrayOfTuple[k][1];

            if (colName === "file_date" || typeof val == 'string') {
                insert += `'${val}'`;
            } else if (typeof val == 'number') {
                insert += `${val}`;
            } else {
                insert += `'${val}'`;
            }
            insert += ",";
        }
        insert = insert.slice(0, -1) + "),\n";
    }
    
    // Remove trailing comma and newline, then add ON CONFLICT clause
    insert = insert.slice(0, -2) + "\n";
    
    const allColumns: string[] = [...Object.keys(data[0]), "file_date"];
    insert += `ON CONFLICT ("Interval", "DateEpochMs") \nDO UPDATE SET \n`;
    for (let i = 0; i < allColumns.length; i++) {
        const col = allColumns[i];
        insert += `    "${col}" = EXCLUDED."${col}"`;
        if (i < allColumns.length - 1) {
            insert += `,`;
        }
        insert += `\n`;
    }
    insert += `;`;

    return insert;
}

async function main() {
    const urlString = process.argv[2]; // "https://rest.fnar.net/exchange/cxpc/ALO.AI1"
    const url = new URL(urlString);
    const segments = url.pathname.split('/');
    const lastSegment = segments[segments.length - 1]; // "ALO.AI1"
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

    await writeFile(jsonFilePath, stringData, 'utf-8');

    let data = await readJsonArray(jsonFilePath);
    if (!data) return;

    let createTable: string = LambdaCreateTable(data, fileNameGeneric);
    let insertTable: string = LambdaInsertTable(data, fileNameGeneric);

    let fullsql = createTable + "\n\n" + insertTable;
    console.log(fullsql);

    const outputFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sql';
    const outputPath = join(outputFolder, getTodayDateFileName(fileNameGeneric, ".sql"));

    const processedFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed';
    const processedFilePath = join(processedFolder, basename(jsonFilePath));

    try {
        await mkdir(outputFolder, { recursive: true });
        await writeFile(outputPath, fullsql, 'utf-8');
        console.log(`Successfully saved SQL file to: ${outputPath}`);

        await mkdir(processedFolder, { recursive: true });
        await rename(jsonFilePath, processedFilePath);
        console.log(`Successfully moved JSON file to: ${processedFilePath}`);
    } catch (error: any) {
        console.error('Error during output or file moving step:', error.message);
    }
}

main();