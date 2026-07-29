import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';

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
  let data = await readJsonArray('/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed/cxpc_AL_AI1_29072026.json');
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
  const outputFolder = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed'; // Change to your desired folder path
  const fileName = 'cxpc_AL_AI1_29072026.sql';
  const outputPath = join(outputFolder, fileName);

  try {
    // Ensure the output folder exists before writing
    await mkdir(outputFolder, { recursive: true });

    // Write the string to the file as UTF-8
    await writeFile(outputPath, sb, 'utf-8');
    console.log(`Successfully saved SQL file to: ${outputPath}`);
  } catch (error) {
    console.error('Error writing SQL file:', error.message);
  }
}

main();