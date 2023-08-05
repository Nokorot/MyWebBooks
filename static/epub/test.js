
download_btn = document.querySelector("button#download-book");
download_btn.addEventListener('click', async () => {
    const JSZip = window.JSZip;
    const zip = new JSZip();

    const mimetype = 'application/epub+zip';
    zip.file('mimetype', mimetype);

    const ctnr = `
    <?xml version="1.0"?>
    <container
        version="1.0"
        xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
       <rootfiles>
          <rootfile
              full-path="EPUB/As_You_Like_It.opf"
              media-type="application/oebps-package+xml"/>
       </rootfiles>
    </container>`;

    // Set metadata for the book
    const metadata = `
      <?xml version="1.0" encoding="UTF-8"?>
      <package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>Your Book Title</dc:title>
          <dc:language>en</dc:language>
          <dc:creator>Your Name</dc:creator>
          
        </metadata>
      </package>
    `;

    // Add the metadata file to the ePub
    zip.file('metadata.opf', metadata);

    // Create and add a new chapter
    const chapter1 = `
      <?xml version="1.0" encoding="UTF-8"?>
      <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>Chapter 1</title></head>
        <body>
          <h1>Chapter 1</h1>
          <p>This is the content of chapter 1.</p>
        </body>
      </html>
    `;

    // Add the chapter file to the ePub
    zip.file('chap_01.xhtml', chapter1);

    // Generate the EPUB file
    const epubBlob = await zip.generateAsync({ type: 'blob' });

    // Save the EPUB file
    saveAs(epubBlob, 'your_book.epub');
});