document.getElementById('deployBtn').onclick = async function() {
    const output = document.getElementById('output');
    output.textContent = 'Running deployment script...';
    try {
        const response = await fetch('/run-script', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            output.textContent = data.output || 'Script finished with no output.';
        } else {
            output.textContent = 'Error:\n' + (data.error || 'Unknown error');
        }
    } catch (err) {
        output.textContent = 'Request failed: ' + err;
    }
};
