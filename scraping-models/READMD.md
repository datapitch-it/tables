Il file 'scrape.sh' esegue un loop dello stesso prompt (_scarica i dati da questi sito_) usando vari modelli di Gemini: 

```
models=(
    "gemini-pro"
    "gemini-1.5-pro-latest"
    "gemini-1.5-flash-latest"
    "gemini-1.5-pro-001"
    "gemini-1.5-flash-001"
    "gemini-1.5-pro-002"
    "gemini-1.5-flash-002"
    "gemini-1.5-flash-8b-latest"
    "gemini-1.5-flash-8b-001"
    "gemini-exp-1114"
    "gemini-exp-1121"
    "gemini-exp-1206"
    "gemini-2.0-flash-exp"
    "gemini-2.0-flash-thinking-exp-1219"
    "gemini-2.0-flash-thinking-exp-01-21"
    "gemini-2.0-flash"
    "gemini-2.0-pro-exp-02-05"
    "gemini-2.0-flash-lite"
    "gemini-2.5-pro-exp-03-25"
)
```

Il file analisi.md evidenzia le principali caratteristiche e differenze tra i vari output, in base ai modelli usati.

Ho raccontato l'esperimento anche su [Substack](https://nelsonmau.substack.com/p/fare-scraping-dallo-stesso-sito-ma)
