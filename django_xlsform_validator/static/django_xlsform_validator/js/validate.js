document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('validation-form');
    const resultsContainer = document.getElementById('results-container');
    const validResult = document.getElementById('valid-result');
    const invalidResult = document.getElementById('invalid-result');
    const errorsTableBody = document.getElementById('errors-table-body');
    const resultsHeader = document.getElementById('results-header');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Validating...';
        
        resultsContainer.classList.add('d-none');
        validResult.classList.add('d-none');
        invalidResult.classList.add('d-none');
        
        const formData = new FormData(form);
        
        fetch('/validator/validate/', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            resultsContainer.classList.remove('d-none');
            
            if (data.result === 'valid') {
                resultsHeader.className = 'card-header bg-success text-white';
                validResult.classList.remove('d-none');
            } else {
                resultsHeader.className = 'card-header bg-danger text-white';
                invalidResult.classList.remove('d-none');
                
                const downloadContainer = document.getElementById('download-link-container');
                const downloadLink = document.getElementById('download-link');
                if (data.download_id) {
                    downloadLink.href = `/validator/validate/download/?id=${data.download_id}`;
                    downloadContainer.classList.remove('d-none');
                } else {
                    downloadContainer.classList.add('d-none');
                }
                
                errorsTableBody.innerHTML = '';
                
                data.errors.forEach(error => {
                    const row = document.createElement('tr');
                    row.className = 'error-row';
                    
                    row.innerHTML = `
                        <td>${error.line}</td>
                        <td>${error.column}</td>
                        <td>${error.question_name || 'N/A'}</td>
                        <td>${formatErrorType(error.error_type)}</td>
                        <td>${error.error_explanation}</td>
                        <td>${error.constraint_message || ''}</td>
                    `;
                    
                    errorsTableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultsContainer.classList.remove('d-none');
            resultsHeader.className = 'card-header bg-danger text-white';
            invalidResult.classList.remove('d-none');
            
            errorsTableBody.innerHTML = '';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="6" class="text-center">
                    An error occurred while validating the spreadsheet. Please try again.
                </td>
            `;
            errorsTableBody.appendChild(row);
        })
        .finally(() => {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        });
    });
    
    function formatErrorType(errorType) {
        switch(errorType) {
            case 'type_mismatch':
                return 'Type Mismatch';
            case 'error_constraint_unsatisfied':
                return 'Constraint Violation';
            case 'error_value_required':
                return 'Required Value Missing';
            default:
                return errorType;
        }
    }
});
