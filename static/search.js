document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('search-form');
    if (form) {
        form.addEventListener('input', function() {
            const formData = new FormData(form);
            const params = new URLSearchParams(formData).toString();
            fetch('/?' + params, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const results = doc.getElementById('results');
                    document.getElementById('results').innerHTML = results.innerHTML;
                });
        });
    }
}); 