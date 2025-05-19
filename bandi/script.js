// Global array to store all the items from all datasets
let allItems = [];
let displayedItems = []; // Separate array to handle the currently displayed (filtered) items
let scrapingTimestamps = {}; // To store the scraping_timestamp for each dataset

// Function to map item keys based on the dataset
function mapItem(item, datasetName) {
    // Extract `custom` object fields for general usage
    const custom = item['custom'] || {};
    switch (datasetName) {
        case 'arter':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: custom['Topics'] ? custom['Topics'].split(', ') : [],
                deadline: item['deadline'] || 'N/A',
                source: 'arter'
            };
        case 'eugrants':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: [custom['category'] || ''], // Using category as a tag
                deadline: item['deadline'] || 'N/A',
                source: 'eugrants',
                identifier: custom['identifier'] || 'N/A',
                publicationDate: custom['pub_date'] || 'N/A'
            };
        case 'eucall':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: custom['category'] ? [custom['category']] : [],
                deadline: item['deadline'] || 'N/A',
                source: 'eucall'
            };
        case 'euportal':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: custom['category'] ? [custom['category']] : [],
                deadline: item['deadline'] || custom['dtstart'] || 'N/A',
                source: 'euportal'
            };
        case 'invitalia':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: custom['Topics'] ? custom['Topics'].split(', ') : [],
                deadline: item['deadline'] || 'N/A',
                source: 'invitalia'
            };
        case 'onepass':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: custom['tags'] || [],
                deadline: item['deadline'] || 'N/A',
                source: 'onepass'
            };
        case 'inpa':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: [], // INPA data has no tags
                deadline: item['deadline'] || 'N/A',
                source: 'inpa'
            };
        case 'journalism':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: [], // journalism data has no tags
                deadline: item['deadline'] || 'N/A',
                source: 'journalism'
            };
        case 'newitems':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: [],
                deadline: item['deadline'] || 'N/A',
                source: 'newitems'
            };
        default:
            return {};
    }
}

// Function to check if the deadline is from today onwards
function isDateFromTodayOnward(deadline) {
    if (!deadline || deadline === 'N/A') {
        return false;
    }

    const today = new Date().setHours(0, 0, 0, 0); 
    const deadlineDate = new Date(deadline).setHours(0, 0, 0, 0);

    return deadlineDate >= today;
}

// Function to load data from a JSON file, filter by date, and add to the global array
function loadDataset(datasetUrl, dataKey, datasetName) {
    return fetch(datasetUrl)
        .then(response => response.json())
        .then(data => {
            scrapingTimestamps[datasetName] = data.scraping_timestamp;

            let items = data[dataKey];
            if (!items || !Array.isArray(items)) {
                console.error("Dataset structure is not as expected", datasetUrl);
                return;
            }

            let filteredItems = items.map(item => mapItem(item, datasetName))
                .filter(mappedItem => isDateFromTodayOnward(mappedItem.deadline));

            allItems = allItems.concat(filteredItems);
        })
        .catch(error => console.error('Error loading dataset:', error));
}

// Function to display the items in the table
function displayItems(items) {
    let rows = '';
    items.forEach(item => {
        rows += `
            <tr>
                <td>${item.deadline}</td>
                <td>${item.source}</td>
                <td>${item.title}</td>
                <td><a href="${item.link}" target="_blank">Link</a></td>
                <td>${item.description}</td>
                <td>${item.tags.join(', ') || 'N/A'}</td>
            </tr>
        `;
    });

    // Update the table and the item count
    document.getElementById('dataTableBody').innerHTML = rows;
    document.getElementById('itemCount').textContent = `Total items displayed: ${items.length}`;
}

// Function to display the scraping timestamps
function displayScrapingTimestamps() {
    let timestampText = `Scraping Date | Arter: ${scrapingTimestamps.arter || 'N/A'} | INPA: ${scrapingTimestamps.inpa || 'N/A'} | Euportal: ${scrapingTimestamps.euportal || 'N/A'} | Eucall: ${scrapingTimestamps.eucall || 'N/A'} | EUGrants&Tenders: ${scrapingTimestamps.eugrants || 'N/A'} | Onepass: ${scrapingTimestamps.onepass || 'N/A'}`;
    document.getElementById('scrapingTimestamps').textContent = timestampText;
}

// Function to sort and display all items in the table
function displaySortedItems() {
    // Sort all items by deadline in ascending order
    allItems.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));

    // Display the sorted items
    displayedItems = [...allItems]; // Copy sorted items to displayedItems
    displayItems(displayedItems);
    displayScrapingTimestamps(); // Display the scraping timestamps after loading
}

// Filter function to search by keywords and by source
function filterItems(keyword, sourceFilter) {
    keyword = keyword.toLowerCase();

    const filteredItems = allItems.filter(item => 
        (item.title.toLowerCase().includes(keyword) ||
        item.description.toLowerCase().includes(keyword) ||
        item.source.toLowerCase().includes(keyword) ||
        item.tags.some(tag => tag.toLowerCase().includes(keyword))) &&
        (sourceFilter === 'all' ? item.source !== 'newitems' : item.source === sourceFilter)
    );

    displayedItems = filteredItems;
    displayItems(displayedItems);
}

// Attach an event listener to the search input field
document.getElementById('searchInput').addEventListener('input', function() {
    const keyword = this.value;
    const sourceFilter = document.getElementById('sourceFilter').value;
    filterItems(keyword, sourceFilter);
});

// Attach an event listener to the source filter dropdown
document.getElementById('sourceFilter').addEventListener('change', function() {
    const sourceFilter = this.value;
    const keyword = document.getElementById('searchInput').value;
    filterItems(keyword, sourceFilter);
});

// Function to convert filtered data to CSV format
function convertToCSV(items) {
    const headers = ['Deadline', 'Source', 'Title', 'Description', 'Tags', 'Link'];
    const csvRows = [headers.join(',')]; // Create CSV header

    items.forEach(item => {
        const values = [
            item.deadline,
            item.source,
            `"${item.title.replace(/"/g, '""')}"`, // Escape quotes
            `"${item.description.replace(/"/g, '""')}"`,
            `"${item.tags.join(', ').replace(/"/g, '""')}"`,
            item.link
        ];
        csvRows.push(values.join(',')); // Add item row to CSV
    });

    return csvRows.join('\n'); // Combine rows with newline
}

// Function to download filtered data as CSV
function downloadCSV() {
    const csvData = convertToCSV(displayedItems);
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'filtered_data.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Attach event listener to the download button
document.getElementById('downloadCSV').addEventListener('click', downloadCSV);

// Load all datasets, including newitems, then display sorted items
Promise.all([
    loadDataset('./data/arter.json', 'data', 'arter'),
    loadDataset('./data/eucall-rss.json', 'data', 'eucall'),
    loadDataset('./data/euportal.json', 'data', 'euportal'),
    loadDataset('./data/invitalia.json', 'data', 'invitalia'),
    loadDataset('./data/onepass.json', 'data', 'onepass'),
    loadDataset('./data/inpa.json', 'data', 'inpa'),
    loadDataset('./data/eugrants.json', 'data', 'eugrants'),
    loadDataset('./data/journalism.json', 'data', 'journalism'),
    loadDataset('./data/newitems.json', 'data', 'newitems') // Newitems dataset loader
]).then(displaySortedItems);
