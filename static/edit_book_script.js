
function submitForm(event) {
    event.preventDefault(); // Prevent the default form submission behavior

    // Get the form data
    var formData = new FormData(event.target);

    // Create a new AJAX request
    var xhr = new XMLHttpRequest();
    xhr.open('POST', "{{ url_for('edit_data', id=id) }}", true);

    // Set the response type if needed
    // xhr.responseType = 'json';

    // Handle the AJAX response
    xhr.onload = function () {
        if (xhr.status === 200) {
            // Successful response
            alert('Form submitted successfully');
            // Optionally, perform additional actions or show a success message
        } else {
            // Error or unexpected response
            alert('Form submission failed');
            // Optionally, show an error message or perform error handling
        }
    };

    // Send the form data
    xhr.send(formData);
}

function onInputFileLoad(fileContent, format) {
    let importedData;
    if (format === 'json') {
        // Parse JSON file
        try {
            importedData = JSON.parse(fileContent);
        } catch (error) {
            console.error('Error parsing JSON file:', error);
            return;
        }
    } else if (format === 'yaml') {
        // Parse YAML file
        try {
            importedData = jsyaml.load(fileContent);
        } catch (error) {
            console.error('Error parsing YAML file:', error);
            return;
        }
    } else {
        console.error('Unsupported file format:', format);
        return;
    }
    
    console.log(importedData);

    
    // Update form fields with imported data
    document.getElementById('title').value = importedData.title || '';
    document.getElementById('author').value = importedData.author || '';
    document.getElementById('ebok_filename').value = importedData.ebok_filename || '';
    document.getElementById('cover_image').value = importedData.cover_image || '';
    document.getElementById('entry_point').value = importedData.entry_point || '';
    document.getElementById('css_filename').value = importedData.css_filename || '';
    document.getElementById('section_css_selector').value = (importedData.chapter && importedData.chapter.section_css_selector) || '';
    document.getElementById('title_css_selector').value = (importedData.chapter && importedData.chapter.title_css_selector) || '';
    document.getElementById('text_css_selector').value = (importedData.chapter && importedData.chapter.text_css_selector) || '';
    document.getElementById('next_chapter_css_selector').value = (importedData.chapter && importedData.chapter.next_chapter_css_selector) || '';

    console.log('Data imported successfully:', importedData);
}

function handleImportFile(e) {
    const file = e.target.files[0];
    const reader = new FileReader();
    
    reader.onload = function (e) {
        const fileContent = e.target.result;
        const importFormat = file.name.split('.').pop().toLowerCase();
        onInputFileLoad(fileContent, importFormat);
   };

   reader.readAsText(file);
}

function exportData() {
    const exportFormat = document.getElementById('export_format').value;
    const formData = {
        id: "{{ data.id }}",
        title: "{{ data.title }}",
        author: "{{ data.author }}",
        epub_filename: "{{ data.epub_filename }}",
        cover_image: "{{ data.cover_image }}",
        css_filename: "{{ data.css_filename }}",
        entry_point: "{{ data.entry_point }}",
        chapter: {
            section_css_selector: "{{ data.chapter.section_css_selector }}",
            title_css_selector: "{{ data.chapter.title_css_selector }}",
            text_css_selector: "{{ data.chapter.text_css_selector }}",
            next_chapter_css_selector: "{{ data.chapter.next_chapter_css_selector }}"
        },
        include_images: "{{ data.include_images }}"
    };

    let exportData;
    if (exportFormat === 'yaml') {
        // Convert data to YAML
        try {
            exportData = jsyaml.dump(formData);
        } catch (error) {
            console.error('Error converting data to YAML:', error);
            return;
        }
    } else if (exportFormat === 'json') {
        // Convert data to JSON
        try {
            exportData = JSON.stringify(formData, null, 2);
        } catch (error) {
            console.error('Error converting data to JSON:', error);
            return;
        }
    }

    // Create a download link
    const blob = new Blob([exportData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'data.' + exportFormat;
    a.click();
    URL.revokeObjectURL(url);
}

