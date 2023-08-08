
download_btn = document.querySelector("button#download-book");
download_btn.addEventListener('click', async () => {
    const JSZip = window.JSZip;
    const zip = new JSZip();
    // mimetype 
    // META-INF
    // -- container.xml

    // this says it is an epub. It must be the first file in the archive so the reader
    // knows from the first bytes that it is an epub.
    const mimetype = 'application/epub+zip';
    zip.file('mimetype', mimetype);

    // this file tells where the content.opf is and must be in the META-INF folder
    const container = `
    <?xml version="1.0"?>
    <container
        version="1.0"
        xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
       <rootfiles>
          <rootfile
              full-path="content/content.opf"
              media-type="application/oebps-package+xml"/>
       </rootfiles>
    </container>`;
    zip.folder('META-INF').file('container.xml', container);

    // three parts to the content.otf: metadata, manifest and spine.
    // metadata needs author, id, language and title.
    // manifest declares all resources to be read by the reader and their types.
    // spine defines the reading order.
    const metadata = `
    <?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" xmlns:opf="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
   <dc:identifier id="BookID" opf:scheme="isbn">978-3-86680-192-9</dc:identifier>
   <dc:identifier>3b622266-b838-4003-bcb8-b126ee6ae1a2</dc:identifier>
   <dc:title>The title</dc:title>
   <dc:language>fr</dc:language>
   <dc:publisher>The publisher</dc:publisher>
   <dc:creator>The author</dc:creator>
   <dc:contributor>A contributor</dc:contributor>
   <dc:description>A description</dc:description>
   <dc:subject>A subject of the publication</dc:subject>
   <dc:subject>Another subject of the publication</dc:subject>
   <dc:rights>© copyright notice</dc:rights>
   <meta property="dcterms:modified">2020-01-01T01:01:01Z</meta>
  </metadata>
  <manifest>
   <item id="coverimage" href="Images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
   <item id="cover" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>
   <item id="toc" href="toc.html" media-type="application/xhtml+xml" properties="nav"/>
   <item id="chapter-1" href="Text/chapter-1.xhtml" media-type="application/xhtml+xml"/>
   <item id="chapter-2" href="Text/chapter-2.xhtml" media-type="application/xhtml+xml"/>
   <item id="css" href="Styles/publication.css" media-type="text/css"/>
   <item id="font1" href="Fonts/Andada-Italic.otf" media-type="application/vnd.ms-opentype"/>
   <item id="font2" href="Fonts/Andada-Regular.otf" media-type="application/vnd.ms-opentype"/>
   <item id="glyph" href="Images/glyph.png" media-type="image/png"/>
  </manifest>
  <spine>
   <itemref idref="cover"/>
   <itemref idref="toc"/>
   <itemref idref="chapter-1"/>
   <itemref idref="chapter-2"/>
  </spine>
</package>
    `;

    zip.folder('content').file('content.opf', metadata);

   async function parse_website(){
        console.log('hi');
          let response = await fetch('https://www.royalroad.com/fiction/36735/the-perfect-run');
          console.log("hey");
          if (response.ok) {
              alert('success');
            let json = await response.json();
          } else {
            alert('http error: ' + response.status);
          }
          console.log(response.text());
        
      return null;
    }
    parse_website();

    // Generate the EPUB file
    const epubBlob = await zip.generateAsync({ type: 'blob' });

    // Save the EPUB file
    saveAs(epubBlob, 'your_book.epub');
});