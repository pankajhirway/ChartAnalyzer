/**
 * Utility functions for exporting data
 */

/**
 * Converts an array of objects to CSV format
 * @param data - Array of objects to convert
 * @returns CSV string
 */
function convertToCSV<T extends Record<string, unknown>>(data: T[]): string {
  if (data.length === 0) {
    return '';
  }

  // Get headers from the first object
  const headers = Object.keys(data[0]);

  // Create header row
  const headerRow = headers.join(',');

  // Create data rows
  const dataRows = data.map((row) => {
    return headers
      .map((header) => {
        const value = row[header];

        // Handle null/undefined
        if (value === null || value === undefined) {
          return '';
        }

        // Handle arrays - join with semicolon
        if (Array.isArray(value)) {
          const escapedValue = value.join('; ').replace(/"/g, '""');
          return `"${escapedValue}"`;
        }

        // Handle objects - convert to JSON string
        if (typeof value === 'object') {
          const escapedValue = JSON.stringify(value).replace(/"/g, '""');
          return `"${escapedValue}"`;
        }

        // Handle strings with commas, quotes, or newlines - wrap in quotes and escape
        if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }

        return String(value);
      })
      .join(',');
  });

  return [headerRow, ...dataRows].join('\n');
}

/**
 * Triggers a browser download for a CSV file
 * @param csvContent - CSV formatted string
 * @param filename - Name of the file to download
 */
function downloadCSV(csvContent: string, filename: string): void {
  try {
    // Create a Blob with the CSV content
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });

    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up the URL object
    URL.revokeObjectURL(url);
  } catch (error) {
    throw new Error(`Failed to download CSV: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Exports an array of objects to a CSV file
 * @param data - Array of objects to export
 * @param filename - Name of the CSV file (will have .csv appended if not present)
 * @throws Error if export fails
 */
export function exportToCsv<T extends Record<string, unknown>>(data: T[], filename: string): void {
  if (!Array.isArray(data)) {
    throw new Error('Data must be an array of objects');
  }

  if (data.length === 0) {
    throw new Error('Cannot export empty data');
  }

  // Ensure filename has .csv extension
  const csvFilename = filename.endsWith('.csv') ? filename : `${filename}.csv`;

  // Convert data to CSV
  const csvContent = convertToCSV(data);

  // Trigger download
  downloadCSV(csvContent, csvFilename);
}
