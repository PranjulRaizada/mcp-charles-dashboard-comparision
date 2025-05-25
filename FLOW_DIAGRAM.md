# Flow Diagrams

## Overall Workflow
```mermaid
graph TD
    A[Charles Proxy Logs] --> B[dashboard_ready_comparison.py]
    B --> C[Generate Comparison Data]
    C --> D[Save to dashboard_data/]
    D --> E[simple_dashboard.py]
    E --> F[Web Dashboard]
    F --> G[View Comparisons]
    G --> H{Select Endpoint}
    H --> I[View Differences]
    I --> J[Request Body]
    I --> K[Headers]
    I --> L[Parameters]
    I --> M[Response]
    I --> N[Status Codes]
```

## Data Processing Flow
```mermaid
graph LR
    A[Input Logs] --> B[Parse Logs]
    B --> C[Extract Endpoints]
    C --> D[Compare Instances]
    D --> E[Generate Differences]
    E --> F[Create Summary]
    F --> G[Save JSON]
    G --> H[Update Index]
```

## Component Architecture
```mermaid
graph TD
    subgraph Frontend
        A[Web UI] --> B[Chart.js]
        A --> C[Bootstrap]
        A --> D[Interactive Tables]
    end
    
    subgraph Backend
        E[Flask Server] --> F[Comparison Engine]
        F --> G[File Parser]
        F --> H[Difference Generator]
        H --> I[Instance Matcher]
        H --> J[Request Comparator]
        H --> K[Response Comparator]
    end
    
    subgraph Storage
        L[dashboard_data/] --> M[Comparison Files]
        L --> N[Index File]
    end
    
    Frontend <--> Backend
    Backend <--> Storage
```

## Diagram Descriptions

### Overall Workflow
This diagram shows the complete flow of data through the system, from the initial Charles Proxy logs to the final difference visualization. It illustrates how users interact with the system and what types of differences they can view.

### Data Processing Flow
This diagram details the internal processing steps that occur when comparing log files. It shows how raw log data is transformed into structured comparison data that can be displayed in the dashboard.

### Component Architecture
This diagram shows the system's architecture divided into three main sections:
- Frontend: The user interface components
- Backend: The server and processing components
- Storage: The data storage components

Each section contains its specific components and shows how they interact with each other. 