function limitWords(element, wordLimit) {
        if (element) {
            const text = element.textContent;
            const words = text.split(/\s+/); // Divide el texto por espacios en blanco
            if (words.length > wordLimit) {
                const limitedText = words.slice(0, wordLimit).join(' ') + '...';
                element.textContent = limitedText;
            }
        }
    }

    // Código nuevo: Selecciona todos los elementos con la clase 'animal-description-limit'
    // document.addEventListener('DOMContentLoaded') asegura que el script se ejecute cuando el DOM esté completamente cargado
    document.addEventListener('DOMContentLoaded', () => {
        const descriptionElements = document.querySelectorAll('.animal-description-limit');
        // Itera sobre cada elemento y aplica la función limitWords
        descriptionElements.forEach(element => {
            limitWords(element, 20); // Limita cada descripción a 20 palabras
        });
    });