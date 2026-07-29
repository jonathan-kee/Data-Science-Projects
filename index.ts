import { readFile } from 'node:fs/promises';

async function readJsonArray(filePath:any) {
  try {
    const data = await readFile(filePath, 'utf-8');
    const jsonArray = JSON.parse(data);

    if (!Array.isArray(jsonArray)) {
      throw new Error('The JSON file does not contain a top-level array.');
    }

    console.log(`Loaded ${jsonArray.length} items successfully!`);
    return jsonArray;
  } catch (error:any) {
    console.error('Failed to read or parse JSON file:', error.message);
  }
}

function getTodayDateFileName(filename:any, extension:any){
  const today = new Date();

  const day   = String(today.getDate()).padStart(2, '0');
  const month = String(today.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
  const year  = today.getFullYear();

  const ddMMyyyy = `${day}${month}${year}`;
  console.log(ddMMyyyy); // Output: "29072026

  return filename + "_" + ddMMyyyy + extension;
} 

function Lambda(data:any){
  console.log(data[0])
  const columns: string[] = Object.keys(data[0])
  const rowValues = Object.values(data[0]);
  for (let i = 0; i < columns.length; i++) {
    console.log(columns[i] + " : " + typeof rowValues[i] + " : " + rowValues[i])
  }
}

async function main() {
  
  // label the data that can be generic
  // generic variables
  let apiGeneric:string = "https://rest.fnar.net/exchange/cxpc/AL.AI1";
  let fileNameGeneric:string = "cxpc_AL_AI1";
  let tableNameGeneric:string = "raw.cxpc_AL_AI1_raw";
  let columnGeneric:string[] = ["Interval", "DateEpochMs", "Open", "Close", "High", "Low", "Volume", "Traded"]
  let lambdaToProcessTheArray;

  const jsonFilePath = '/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed/' + getTodayDateFileName(fileNameGeneric, ".json");

  // Read file on disk
  let data = await readJsonArray(jsonFilePath);
  if (!data) return;

  Lambda(data);
}

main();