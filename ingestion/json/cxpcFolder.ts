import { readFile, writeFile, mkdir, rename, readdir } from 'node:fs/promises';
import { join, basename } from 'node:path';

async function readJsonArray(filePath: any) {
    try {
        const data = await readFile(filePath, 'utf-8');
        const jsonArray = JSON.parse(data);

        if (!Array.isArray(jsonArray)) {
            throw new Error('The JSON file does not contain a top-level array.');
        }

        console.log(`Loaded ${jsonArray.length} items successfully from ${basename(filePath)}!`);
        return jsonArray;
    } catch (error: any) {
        console.error(`Failed to read or parse JSON file ${basename(filePath)}:`, error.message);
    }
}

function LambdaCreateTable(data: any, tablename: string) {
    const columns: string[] = Object.keys(data[0]);
    const rowValues = Object.values(data[0]);
    let arrayOfTuple: [string, string, any][] = [];

    for (let i = 0; i < columns.length; i++) {
        if (typeof rowValues[i] == 'string') {
            arrayOfTuple.push([columns[i], "varchar(20)", rowValues[i]]);
        } else if (typeof rowValues[i] == 'number') {
            arrayOfTuple.push([columns[i], "numeric(15, 2)", rowValues[i]]);
        } else {
            arrayOfTuple.push([columns[i], "varchar(20)", rowValues[i]]);
        }
    }

    let createTable = `CREATE TABLE IF NOT EXISTS raw.` + tablename + `\n(\n`;
    for (let i = 0; i < arrayOfTuple.length; i++) {
        createTable += `    "${arrayOfTuple[i][0]}"      ${arrayOfTuple[i][1]},\n`;
    }
    
    // Add metadata column for file date tracking
    createTable += `    "file_date"      date,\n`;
    
    // Add composite primary key constraint for idempotency
    createTable += `    CONSTRAINT pk_${tablename} PRIMARY KEY ("Interval", "DateEpochMs")\n`;
    createTable += `);`;
    
    return createTable;
}

function LambdaInsertTable(data: any, tablename: string, formattedDate: string) {
    const lengthOfData = data.length;
    let insert = ``; // Removed TRUNCATE TABLE for safe incremental/idempotent runs

    for (let i = 0; i < lengthOfData; i++) {
        const columns: string[] = Object.keys(data[i]);
        const rowValues = Object.values(data[i]);
        let arrayOfTuple: [string, string, any][] = [];

        for (let j = 0; j < columns.length; j++) {
            if (typeof rowValues[j] == 'string') {
                arrayOfTuple.push([columns[j], "varchar(20)", rowValues[j]]);
            } else if (typeof rowValues[j] == 'number') {
                arrayOfTuple.push([columns[j], "numeric(15, 2)", rowValues[j]]);
            } else {
                arrayOfTuple.push([columns[j], "varchar(20)", rowValues[j]]);
            }
        }
        
        // Push file_date metadata entry into the values array
        arrayOfTuple.push(["file_date", "date", formattedDate]);

        if (i == 0) {
            let insertParenthesis = "(";
            for (let k = 0; k < arrayOfTuple.length; k++) {
                insertParenthesis += `"${arrayOfTuple[k][0]}",`;
            }
            insertParenthesis = insertParenthesis.slice(0, -1) + ")\nVALUES\n";

            insert += `INSERT INTO raw.${tablename} ` + insertParenthesis;
        }

        insert += `    (`;
        for (let k = 0; k < arrayOfTuple.length; k++) {
            if (arrayOfTuple[k][0] === "file_date") {
                insert += `'${arrayOfTuple[k][2]}'`;
            } else if (typeof arrayOfTuple[k][2] == 'string') {
                insert += `'${arrayOfTuple[k][2]}'`;
            } else if (typeof arrayOfTuple[k][2] == 'number') {
                insert += `${arrayOfTuple[k][2]}`;
            }
            insert += ",";
        }
        insert = insert.slice(0, -1) + "),\n";
    }
    insert = insert.slice(0, -2) + `\n`;

    // Append ON CONFLICT DO UPDATE clause for upsert functionality
    insert += `ON CONFLICT ("Interval", "DateEpochMs") \n`;
    insert += `DO UPDATE SET \n`;

    const sampleKeys = Object.keys(data[0]);
    let updateSet = "";
    for (const col of sampleKeys) {
        updateSet += `    "${col}" = EXCLUDED."${col}",\n`;
    }
    updateSet += `    "file_date" = EXCLUDED."file_date";`;

    insert += updateSet;
    return insert;
}

async function main() {
    const inputFolder = process.argv[2] || '/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed';
    const outputFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sql';
    const processedFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed';

    try {
        const files = await readdir(inputFolder);
        const targetFiles = files.filter(file => /^.*AI1_\d{8}\.json$/.test(file));

        if (targetFiles.length === 0) {
            console.log('No files matching the pattern *AI1_DDMMYYYY.json found in the directory.');
            return;
        }

        for (const file of targetFiles) {
            const jsonFilePath = join(inputFolder, file);
            const fileNameGeneric: string = basename(file, '.json');

            // 1. Transform table name: cxpc_afr_ai1_raw
            const baseWithoutDate = fileNameGeneric.split('_')[0]; 
            const tableName = `cxpc_${baseWithoutDate.replace('.', '_')}_raw`.toLowerCase();

            // 2. Extract prefix and file date format (DDMMYYYY -> YYYY-MM-DD)
            const [filePrefix, fileDate] = fileNameGeneric.split('_');
            const filePrefixClean = filePrefix.split('.')[0]; 
            const customOutputName = `cxpc_${filePrefixClean}_AI1_${fileDate}`;

            // Convert DDMMYYYY (e.g. 16082026) to SQL Date format YYYY-MM-DD (2026-08-16)
            const day = fileDate.substring(0, 2);
            const month = fileDate.substring(2, 4);
            const year = fileDate.substring(4, 8);
            const formattedDate = `${year}-${month}-${day}`;

            // Read file on disk
            let data = await readJsonArray(jsonFilePath);
            if (!data) continue;

            let createTable: string = LambdaCreateTable(data, tableName);
            let insertTable: string = LambdaInsertTable(data, tableName, formattedDate);

            let fullsql = createTable + "\n\n" + insertTable;
            console.log(fullsql);

            // --- Output section ---
            const outputPath = join(outputFolder, `${customOutputName}.sql`);
            const processedFilePath = join(processedFolder, file);

            try {
                await mkdir(outputFolder, { recursive: true });
                await writeFile(outputPath, fullsql, 'utf-8');
                console.log(`Successfully saved SQL file to: ${outputPath}`);

                await mkdir(processedFolder, { recursive: true });
                await rename(jsonFilePath, processedFilePath);
                console.log(`Successfully moved JSON file to: ${processedFilePath}`);
            } catch (error: any) {
                console.error(`Error during output or file moving step for ${file}:`, error.message);
            }
        }
    } catch (error: any) {
        console.error('Error reading input directory:', error.message);
    }
}

main();