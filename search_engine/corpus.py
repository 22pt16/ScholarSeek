"""
Research-paper corpus for ScholarSeek.

The corpus is designed for demonstrating information retrieval
over research literature, with emphasis on AI and cybersecurity.
"""

SAMPLE_CORPUS = [
    {
        "id": "paper_01",
        "title": "Phishing Detection Leveraging Machine Learning and Deep Learning: A Review",
        "category": "Cybersecurity",
        "url": "https://arxiv.org/abs/2205.07411",
        "content": (
            "Phishing attacks trick victims into disclosing sensitive information. "
            "Machine learning and deep learning approaches can be used to detect "
            "phishing attacks using different types of data and deployment strategies. "
            "The study reviews machine learning models for phishing detection "
            "and discusses their advantages and limitations."
        )
    },

    {
        "id": "paper_02",
        "title": "Machine Learning for Detection and Mitigation of Web Vulnerabilities and Web Attacks",
        "category": "Web Security",
        "url": "https://arxiv.org/abs/2304.14451",
        "content": (
            "Machine learning techniques have been applied to the detection and "
            "mitigation of web vulnerabilities and attacks including cross-site "
            "scripting and cross-site request forgery. The research explores "
            "different machine learning approaches for identifying web attacks "
            "and discusses challenges in detecting evolving vulnerabilities."
        )
    },

    {
        "id": "paper_03",
        "title": "AlgoXSSF: Detection and Analysis of XSRF and XSS Attacks via Machine Learning Algorithms",
        "category": "Web Security",
        "url": "https://arxiv.org/abs/2402.01012",
        "content": (
            "Cross-site scripting and cross-site request forgery are important "
            "web security threats. Machine learning and artificial intelligence "
            "can be used to identify malicious patterns and improve automated "
            "web attack detection. The proposed framework investigates machine "
            "learning algorithms for detecting and analysing XSS and XSRF attacks."
        )
    },

    {
        "id": "paper_04",
        "title": "Leveraging LLM to Strengthen ML-Based Cross-Site Scripting Detection",
        "category": "Web Security",
        "url": "https://arxiv.org/abs/2504.21045",
        "content": (
            "Cross-site scripting remains an important web security vulnerability. "
            "Machine learning models can identify malicious XSS samples, but "
            "obfuscated attacks can reduce detection performance. The study "
            "investigates generating diverse obfuscated XSS samples to improve "
            "machine learning based detection."
        )
    },

    {
        "id": "paper_05",
        "title": "XGBoost: A Scalable Tree Boosting System",
        "category": "Machine Learning",
        "url": "https://arxiv.org/abs/1603.02754",
        "content": (
            "XGBoost is a scalable tree boosting system designed for efficient "
            "machine learning. The system introduces techniques including "
            "sparsity-aware learning and weighted quantile sketching. Its design "
            "allows gradient tree boosting to scale to large datasets."
        )
    },

    {
        "id": "paper_06",
        "title": "Email Summarization to Assist Users in Phishing Identification",
        "category": "Cybersecurity",
        "url": "https://arxiv.org/abs/2203.13380",
        "content": (
            "Phishing emails can use sophisticated social engineering techniques "
            "to deceive users. Machine learning and natural language processing "
            "can analyse email content and assist users in identifying malicious "
            "intent. The research investigates human-centric support for phishing "
            "identification using email analysis and summarization."
        )
    },

    {
        "id": "paper_07",
        "title": "Deep Learning Based Intrusion Detection",
        "category": "Network Security",
        "url": "https://arxiv.org/",
        "content": (
            "Intrusion detection systems identify suspicious or malicious activity "
            "in computer networks. Deep learning models can learn representations "
            "of network traffic and identify anomalous behaviour. Intrusion detection "
            "research commonly evaluates classification accuracy, precision, recall "
            "and false positive rates."
        )
    },

    {
        "id": "paper_08",
        "title": "Machine Learning for Malware Detection",
        "category": "Malware Analysis",
        "url": "https://arxiv.org/",
        "content": (
            "Malware detection uses computational techniques to identify malicious "
            "software and suspicious behaviour. Machine learning models can learn "
            "patterns from executable files, system behaviour and network activity. "
            "Feature extraction and classification are important components of "
            "automated malware detection systems."
        )
    }
]