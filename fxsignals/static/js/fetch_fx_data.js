document.getElementById("fetchDataButton").addEventListener("click", function() {
    fetch(getFxDataUrl, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.text())  // Expecting text response now, not JSON
    .then(htmlTable => {
        // Insert the HTML table into the container
        document.getElementById("tableContainer").innerHTML = htmlTable;
    })
    .catch(error => console.error('Error:', error));
});
