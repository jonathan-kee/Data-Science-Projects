import { readFile, writeFile, mkdir, rename } from 'node:fs/promises';
import { join, basename } from 'node:path';

async function readJsonArray(filePath) {
  try {
    const data = await readFile(filePath, 'utf-8');
    const jsonArray = JSON.parse(data);

    if (!Array.isArray(jsonArray)) {
      throw new Error('The JSON file does not contain a top-level array.');
    }

    console.log(`Loaded ${jsonArray.length} items successfully!`);
    return jsonArray;
  } catch (error) {
    console.error('Failed to read or parse JSON file:', error.message);
  }
}

async function main() {
  const jsonFilePath = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed/cxpc_AL_AI1_29072026.json';
  
  let data = await readJsonArray(jsonFilePath);
  if (!data) return;

  let lengthOfArrayOfJson = data.length;

  const tableName = 'raw.cxpc_AL_AI1_raw';
  
  // 1. Initialize string with TRUNCATE TABLE statement
  let sb = `TRUNCATE TABLE ${tableName};\n\n`;
  
  // 2. Add INSERT statement header
  sb += `INSERT INTO ${tableName} ("Interval", "DateEpochMs", "Open", "Close", "High", "Low", "Volume", "Traded")\nVALUES `;

  for (let i = 0; i < lengthOfArrayOfJson; i++) {
    sb += `('${data[i].Interval}',${data[i].DateEpochMs},${data[i].Open},${data[i].Close},${data[i].High},${data[i].Low},${data[i].Volume},${data[i].Traded}),\n`;
  }

  sb = sb.slice(0, -2) + ';';

  // --- Output section ---
  const outputFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sql';
  const fileName = 'cxpc_AL_AI1_29072026.sql';
  const outputPath = join(outputFolder, fileName);

  // --- Processed JSON target directory ---
  const processedFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed';
  const processedFilePath = join(processedFolder, basename(jsonFilePath));

  try {
    // 1. Ensure the SQL output folder exists and write the SQL file
    await mkdir(outputFolder, { recursive: true });
    await writeFile(outputPath, sb, 'utf-8');
    console.log(`Successfully saved SQL file to: ${outputPath}`);

    // 2. Ensure the processed folder exists and move the JSON file
    await mkdir(processedFolder, { recursive: true });
    await rename(jsonFilePath, processedFilePath);
    console.log(`Successfully moved JSON file to: ${processedFilePath}`);

  } catch (error) {
    console.error('Error during output or file moving step:', error.message);
  }
}

main();