document.getElementById('showResults').addEventListener('click', function() {
    document.getElementById('results').style.display = 'block';
    document.getElementById('errors').style.display = 'none';
});

document.getElementById('showErrors').addEventListener('click', function() {
    document.getElementById('errors').style.display = 'block';
    document.getElementById('results').style.display = 'none';
});

