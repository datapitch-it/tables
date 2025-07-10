// Global array to store all the items from all datasets
let allItems = [];
let displayedItems = []; // Separate array to handle the currently displayed (filtered) items
let scrapingTimestamps = {}; // To store the scraping_timestamp for each dataset
// Variabile per tenere traccia dell'ordinamento della scadenza (true = ascendente, false = discendente)
let isDeadlineSortAscending = true;

// Funzione per troncare il testo a una lunghezza massima specificata, aggiungendo puntini
// Nota: questa funzione non è più usata per il troncamento della descrizione nelle card con il "Leggi tutto",
// ma è mantenuta per completezza se volessi usarla altrove nel tuo codice.
function truncateText(text, maxLength) {
    if (!text) {
        return ''; // Gestisce il caso in cui il testo sia nullo o indefinito
    }
    if (text.length > maxLength) {
        return text.substring(0, maxLength) + '...';
    }
    return text;
}

// Funzione helper per pulire e formattare la descrizione, convertendo i tag <p> e le newline in <br>
function cleanAndFormatDescription(description) {
    if (!description) {
        return '';
    }
    // Rimuovi i tag <p> e </p> e rimpiazzali con newline per coerenza
    let cleaned = description.replace(/<\/?p>/g, '\n').trim();
    // Rimuovi spazi extra o newline consecutive
    cleaned = cleaned.replace(/\n\s*\n/g, '\n').trim();
    return cleaned;
}

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
        case 'lombardia':
            return {
                title: item['title'] || 'N/A',
                description: item['description'] || 'N/A',
                link: item['link'] || '#',
                tags: [], // lomardy data has no tags
                deadline: item['deadline'] || 'N/A',
                source: 'lombardia'
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
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset to the beginning of today
    const deadlineDate = new Date(deadline);
    deadlineDate.setHours(0, 0, 0, 0); // Reset to the beginning of the deadline day
    return deadlineDate >= today;
}

// Funzione per verificare se la data di scadenza è entro i prossimi 30 giorni (inclusi oggi)
function isWithinNext30Days(deadline) {
    if (!deadline || deadline === 'N/A') {
        return false; // Items with invalid/N/A deadlines do not fall into this category
    }
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset to the beginning of today
    const deadlineDate = new Date(deadline);
    deadlineDate.setHours(0, 0, 0, 0); // Reset to the beginning of the deadline day
    // Calculate the date 30 days from now
    const thirtyDaysFromNow = new Date(today);
    thirtyDaysFromNow.setDate(today.getDate() + 30);
    thirtyDaysFromNow.setHours(0, 0, 0, 0);
    // An item is within the next 30 days if its deadline is from today up to (and including) thirtyDaysFromNow
    return deadlineDate >= today && deadlineDate <= thirtyDaysFromNow;
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
    // Update the table
    document.getElementById('dataTableBody').innerHTML = rows;
    // The item count is now updated in applyCurrentSortAndDisplay()
}

// Function to display the items in card format
function displayCards(items) {
    const cardView = document.getElementById('cardView');
    cardView.innerHTML = ''; // Clear existing cards

    const TRUNCATE_LENGTH = 500; // Define the maximum visible length for the description (characters)

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'col-12 mb-4'; // Full width for each card

        // Prepare the description, cleaning it from existing <p> tags and handling newlines
        const cleanedDescription = cleanAndFormatDescription(item.description);

        let descriptionContentHtml = '';

        if (cleanedDescription.length > TRUNCATE_LENGTH) {
            const shortText = cleanedDescription.substring(0, TRUNCATE_LENGTH);
            const longText = cleanedDescription.substring(TRUNCATE_LENGTH);

            // Replace newlines with <br> for HTML display
            const shortHtml = shortText.replace(/\n/g, '<br>');
            const longHtml = longText.replace(/\n/g, '<br>');

            descriptionContentHtml = `
                <p class="card-text">
                    <span class="short-description">${shortHtml}</span><span class="read-more-dots">...</span><span class="full-description d-none">${longHtml}</span>
                    <a href="#" class="read-more-btn text-primary ms-2" data-bs-toggle="collapse" aria-expanded="false" aria-controls="collapseDescription">Leggi tutto</a>
                </p>
            `;
        } else {
            // If the description is short, display it entirely with <br> for newlines
            descriptionContentHtml = `<p class="card-text">${cleanedDescription.replace(/\n/g, '<br>') || 'N/A'}</p>`;
        }

        card.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">DEADLINE: ${item.deadline} | SOURCE: ${item.source}</h6>
                    <a href="${item.link}" class="card-title" target="_blank"><h5 class="text-primary">${item.title}</h5></a>
                    ${descriptionContentHtml}
                    <p class="card-text"><small class="text-muted">${item.tags.join(', ') || 'N/A'}</small></p>
                </div>
            </div>
        `;
        cardView.appendChild(card);
    });

    // Attach listeners for "Read More" buttons after cards are rendered
    attachReadMoreListeners();
}

// Funzione per allegare i listener ai pulsanti "Leggi tutto"
function attachReadMoreListeners() {
    document.querySelectorAll('.read-more-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault(); // Prevents the default link behavior

            const parentText = this.closest('.card-text'); // Find the parent paragraph
            const shortSpan = parentText.querySelector('.short-description');
            const dotsSpan = parentText.querySelector('.read-more-dots');
            const fullSpan = parentText.querySelector('.full-description');

            if (fullSpan.classList.contains('d-none')) {
                // If it's hidden (meaning we are in "Read More" state)
                fullSpan.classList.remove('d-none'); // Show the full text
                dotsSpan.classList.add('d-none');   // Hide the dots
                this.textContent = 'Mostra meno';   // Change the button text
            } else {
                // If it's visible (meaning we are in "Show Less" state)
                fullSpan.classList.add('d-none');    // Hide the full text
                dotsSpan.classList.remove('d-none'); // Show the dots
                this.textContent = 'Leggi tutto';   // Change the button text
            }
        });
    });
}

// Function to display the scraping timestamps
function displayScrapingTimestamps() {
    let timestampText = `Scraping Date | Arter: ${scrapingTimestamps.arter || 'N/A'} | INPA: ${scrapingTimestamps.inpa || 'N/A'} | Euportal: ${scrapingTimestamps.euportal || 'N/A'} | Eucall: ${scrapingTimestamps.eucall || 'N/A'} | EUGrants&Tenders: ${scrapingTimestamps.eugrants || 'N/A'} | Onepass: ${scrapingTimestamps.onepass || 'N/A'} | Journalism: ${scrapingTimestamps.journalism || 'N/A'} | Lombardia: ${scrapingTimestamps.lombardia || 'N/A'}`;
    document.getElementById('scrapingTimestamps').textContent = timestampText;
}

// Funzione per applicare l'ordinamento corrente e visualizzare gli item
// Questa funzione opera su `displayedItems`
function applyCurrentSortAndDisplay() {
    // Ordina gli elementi attualmente visualizzati (displayedItems)
    displayedItems.sort((a, b) => {
        const dateA = a.deadline === 'N/A' ? new Date('9999-12-31') : new Date(a.deadline); // Treat N/A as very far in the future
        const dateB = b.deadline === 'N/A' ? new Date('9999-12-31') : new Date(b.deadline);
        // Applica l'ordinamento in base a isDeadlineSortAscending
        return isDeadlineSortAscending ? (dateA - dateB) : (dateB - dateA);
    });

    // Check the current view and display items accordingly
    if (document.getElementById('tableView').classList.contains('d-none')) {
        displayCards(displayedItems);
    } else {
        displayItems(displayedItems);
    }

    // Update the item count for both views
    document.getElementById('itemCount').textContent = `Total items displayed: ${displayedItems.length}`;

    displayScrapingTimestamps(); // Display the scraping timestamps after loading
}

// Funzione per filtrare gli item per parola chiave, fonte e scadenza
function filterItems(keyword, sourceFilter, deadlineFilter) {
    keyword = keyword.toLowerCase();
    // Filtra sempre da allItems, per poi applicare l'ordinamento
    const tempFilteredItems = allItems.filter(item => {
        const matchesKeyword = (
            item.title.toLowerCase().includes(keyword) ||
            item.description.toLowerCase().includes(keyword) ||
            item.source.toLowerCase().includes(keyword) ||
            item.tags.some(tag => tag.toLowerCase().includes(keyword))
        );
        const matchesSource = (
            sourceFilter === 'all' ? item.source !== 'newitems' : item.source === sourceFilter
        );
        let matchesDeadline = true; // By default, the item matches the deadline filter
        if (deadlineFilter === 'next30days') {
            matchesDeadline = isWithinNext30Days(item.deadline);
        } else if (deadlineFilter === 'beyond30days') {
            matchesDeadline = !isWithinNext30Days(item.deadline) && isDateFromTodayOnward(item.deadline);
        }
        // If deadlineFilter is 'all' or not specified, matchesDeadline remains true
        return matchesKeyword && matchesSource && matchesDeadline;
    });
    // Assegna il risultato del filtro a displayedItems
    displayedItems = tempFilteredItems;

    // Ora applica l'ordinamento e visualizza
    applyCurrentSortAndDisplay();
}

// Funzione helper per aggiornare tutti i filtri
// Aggiunto un parametro per sapere da quale filtro è stata invocata la funzione
function updateFilters(invokingFilter = null) {
    const keyword = document.getElementById('searchInput').value;
    const sourceFilter = document.getElementById('sourceFilter').value;

    // Recupera il valore del filtro scadenza corrente per la logica dei bottoni
    let deadlineFilter = 'all'; // Valore di default
    const currentActiveDeadlineButton = document.querySelector('.btn-group button.active');
    if (currentActiveDeadlineButton && currentActiveDeadlineButton.dataset.deadlineFilter) {
        deadlineFilter = currentActiveDeadlineButton.dataset.deadlineFilter;
    }
    // Se l'invocazione viene da un bottone di filtro scadenza, aggiorna il valore
    if (['all', 'next30days', 'beyond30days'].includes(invokingFilter)) {
        deadlineFilter = invokingFilter;
    }
    // Applica i filtri
    filterItems(keyword, sourceFilter, deadlineFilter);
    // Gestisci le classi 'active' per i bottoni del filtro scadenza
    document.querySelectorAll('.btn-group button').forEach(button => {
        if (button.dataset.deadlineFilter === deadlineFilter) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
}

// Attach event listener to the search input field
document.getElementById('searchInput').addEventListener('input', () => updateFilters());
// Attach event listener to the source filter dropdown
document.getElementById('sourceFilter').addEventListener('change', () => updateFilters());
// Attach event listeners to the new deadline filter buttons
document.getElementById('filterAllDeadlines').addEventListener('click', () => updateFilters('all'));
document.getElementById('filterNext30Days').addEventListener('click', () => updateFilters('next30days'));
document.getElementById('filterBeyond30Days').addEventListener('click', () => updateFilters('beyond30days'));
// Event listener per il pulsante toggle di ordinamento della scadenza
document.getElementById('sortDeadlineToggle').addEventListener('click', () => {
    isDeadlineSortAscending = !isDeadlineSortAscending; // Inverti la direzione
    const sortButton = document.getElementById('sortDeadlineToggle');

    // Aggiorna il testo e la classe CSS del pulsante
    if (isDeadlineSortAscending) {
        sortButton.textContent = 'Deadline Ordine: Crescente';
        sortButton.classList.remove('desc');
        sortButton.classList.add('asc');
    } else {
        sortButton.textContent = 'Deadline Ordine: Decrescente';
        sortButton.classList.remove('asc');
        sortButton.classList.add('desc');
    }

    // Riapplica l'ordinamento e la visualizzazione con la nuova direzione
    applyCurrentSortAndDisplay();
});

// Function to convert filtered data to CSV format
function convertToCSV(items) {
    const headers = ['Deadline', 'Source', 'Title', 'Description', 'Tags', 'Link'];
    const csvRows = [headers.join(',')]; // Create CSV header
    items.forEach(item => {
        // Use cleanAndFormatDescription to get plain text for CSV, then escape quotes
        const descriptionForCsv = cleanAndFormatDescription(item.description).replace(/"/g, '""');
        const values = [
            item.deadline,
            item.source,
            `"${item.title.replace(/"/g, '""')}"`, // Escape quotes
            `"${descriptionForCsv}"`, // Use cleaned description for CSV
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

// Attach event listeners to the view switch buttons
document.getElementById('viewTable').addEventListener('click', () => {
    document.getElementById('tableView').classList.remove('d-none');
    document.getElementById('cardView').classList.add('d-none');
    document.getElementById('viewTable').classList.add('active');
    document.getElementById('viewCards').classList.remove('active');
    applyCurrentSortAndDisplay(); // Re-render with current filters and sort
});

document.getElementById('viewCards').addEventListener('click', () => {
    document.getElementById('tableView').classList.add('d-none');
    document.getElementById('cardView').classList.remove('d-none');
    document.getElementById('viewTable').classList.remove('active');
    document.getElementById('viewCards').classList.add('active');
    applyCurrentSortAndDisplay(); // Re-render with current filters and sort
});

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
    loadDataset('./data/regione_lombardia.json', 'data', 'lombardia'),
    loadDataset('./data/newitems.json', 'data', 'newitems') // Newitems dataset loader
]).then(() => {
    // After loading all data, initialize filters (which in turn will call initial sorting)
    updateFilters('all'); // Set the default deadline filter to 'all'

    // Set default view to Card View and activate the button
    document.getElementById('tableView').classList.add('d-none'); // Hide table view
    document.getElementById('cardView').classList.remove('d-none'); // Show card view
    document.getElementById('viewTable').classList.remove('active'); // Deactivate table button
    document.getElementById('viewCards').classList.add('active'); // Activate card button

    applyCurrentSortAndDisplay(); // Ensure cards are displayed with current sorting and count
});