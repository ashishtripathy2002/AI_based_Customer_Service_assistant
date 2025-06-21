# __Customer Service Assistant NLP Architecture__

__App Overview__

``` mermaid
  graph LR;
    A[Customer] -->|Interacts with| C[Agent];
    C -->|Textual Data| D[Backend];
    D --> E[NLP AI Models];
    E --> D;
    D -->|Analysis| C;
    C -->|Interacts with| A;
```



__Backend-AI Model interaction__
``` mermaid
  graph LR;
    A[Backend] -->|Payload| B[Docker Hosted APIs];
    B -->|Response| A;
    A[Backend] -->|Payload| C[FastAPI Hosted APIs];
    C -->|Response| A;
    B --> D[Prefect + MLFlow Servers];
    
   

```

<div class="grid cards" markdown>
  - [__<- Table of Content__](index.md)
  - [__App Functionality ->__](functionality.md)
</div>