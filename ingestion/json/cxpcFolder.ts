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

function getTodayDateFileName(filename: string, extension: string) {
    const today = new Date();

    const day = String(today.getDate()).padStart(2, '0');
    const month = String(today.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
    const year = today.getFullYear();

    const ddMMyyyy = `${day}${month}${year}`;
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

    let createTable = `CREATE TABLE IF NOT EXISTS raw.` + tablename + `\n(\n`
    for (let i = 0; i < arrayOfTuple.length; i++) {
        createTable += '"' + arrayOfTuple[i][0] + '"      ' + arrayOfTuple[i][1] + ',\n'
    }
    createTable = createTable.slice(0, -2) + '\n);';
    return createTable;
}

function LambdaInsertTable(data: any, tablename: string) {
    const lengthOfData = data.length
    let insert = `TRUNCATE TABLE raw.${tablename};\n\n`;

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
            for (let k = 0; k < arrayOfTuple.length; k++) {
                insertParenthesis += '"' + arrayOfTuple[k][0] + '"' + ","
            }
            insertParenthesis = insertParenthesis.slice(0, -1) + ")\nVALUES "

            insert += `INSERT INTO raw.${tablename} ` + insertParenthesis
        }

        insert += "("
        for (let k = 0; k < arrayOfTuple.length; k++) {
            if (typeof arrayOfTuple[k][2] == 'string') {
                insert += `'${arrayOfTuple[k][2]}'`;
            } else if (typeof arrayOfTuple[k][2] == 'number') {
                insert += `${arrayOfTuple[k][2]}`;
            }
            insert += ","
        }
        insert = insert.slice(0, -1) + "),\n"
    }
    insert = insert.slice(0, -2) + ';';
    return insert;
}

async function main() {
    const inputFolder = process.argv[2] || '/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed';
    const outputFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sql';
    const processedFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed';

    try {
        const files = await readdir(inputFolder);
        // Filter files matching the date-suffixed naming convention (e.g., AFR.AI1_16082026.json)
        const targetFiles = files.filter(file => /^.*AI1_\d{8}\.json$/.test(file));

        if (targetFiles.length === 0) {
            console.log('No files matching the pattern *AI1_DDMMYYYY.json found in the directory.');
            return;
        }

        for (const file of targetFiles) {
            const jsonFilePath = join(inputFolder, file);
            
            // Derive generic base name (e.g., AFR.AI1_16082026)
            const fileNameGeneric: string = basename(file, '.json');

            // 1. Transform table name: cxpc_afr_ai1_raw, cxpc_al_ai1_raw, etc.
            const baseWithoutDate = fileNameGeneric.split('_')[0]; // e.g. AFR.AI1
            const tableName = `cxpc_${baseWithoutDate.replace('.', '_')}_raw`.toLowerCase();

            // 2. Transform output SQL filename format: cxpc_BFR_AI1_${TODAY}, cxpc_RGO_AI1_${TODAY}, etc.
            // Extracts prefix (e.g., AFR) and date portion (e.g., 16082026) from the input file
            const [filePrefix, fileDate] = fileNameGeneric.split('_');
            const filePrefixClean = filePrefix.split('.')[0]; // Gets 'AFR' from 'AFR.AI1'
            const customOutputName = `cxpc_${filePrefixClean}_AI1_${fileDate}`;

            // Read file on disk
            let data = await readJsonArray(jsonFilePath);
            if (!data) continue;

            let createTable: string = LambdaCreateTable(data, tableName);
            let insertTable: string = LambdaInsertTable(data, tableName);

            let fullsql = createTable + "\n\n" + insertTable;
            console.log(fullsql);

            // --- Output section ---
            const outputPath = join(outputFolder, `${customOutputName}.sql`);
            const processedFilePath = join(processedFolder, file);

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
                console.error(`Error during output or file moving step for ${file}:`, error.message);
            }
        }
    } catch (error: any) {
        console.error('Error reading input directory:', error.message);
    }
}

main();