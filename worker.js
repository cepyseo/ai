// URL'den prompt parametresini alma fonksiyonu
function getPromptFromUrl(url) {
    const path = new URL(url).pathname;
    const prompt = path.substring(path.lastIndexOf('/') + 1);
    return decodeURIComponent(prompt);
}

// Ana işleyici fonksiyonu
async function handleRequest(request) {
    try {
        const prompt = getPromptFromUrl(request.url);
        
        if (!prompt) {
            return new Response('Prompt bulunamadı', { status: 400 });
        }

        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": "Bearer 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",
                "HTTP-Referer": "https://cepyseo.github.io",
                "X-Title": "CepyAI",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "model": "meta-llama/llama-3.2-1b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        });

        const data = await response.json();
        
        // CORS başlıklarını ekle
        const headers = new Headers({
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        });

        return new Response(JSON.stringify(data), { headers });
    } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
            status: 500,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
        });
    }
}

// Event listener
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
});
