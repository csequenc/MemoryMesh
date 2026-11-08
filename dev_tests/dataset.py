
DATASET = [
    # 1. Independent facts (5)
    {
        "id": 1,
        "input": "The Atlas project uses PostgreSQL as its database.",
        "category": "independent",
        "expected": "ADD",
    },
    {
        "id": 2,
        "input": "The Nova application uses Redis for caching.",
        "category": "independent",
        "expected": "ADD",
    },
    {
        "id": 3,
        "input": "The Orion API is built with FastAPI.",
        "category": "independent",
        "expected": "ADD",
    },
    {
        "id": 4,
        "input": "The Phoenix frontend uses React.",
        "category": "independent",
        "expected": "ADD",
    },
    {
        "id": 5,
        "input": "The Mercury project uses FAISS for vector search.",
        "category": "independent",
        "expected": "ADD",
    },

    # 2. Exact and semantic duplicates (5)
    {
        "id": 6,
        "input": "The Atlas project uses PostgreSQL as its database.",
        "category": "duplicate",
        "expected": "DUPLICATE",
    },
    {
        "id": 7,
        "input": "PostgreSQL is the database used by Atlas.",
        "category": "duplicate",
        "expected": "DUPLICATE",
    },
    {
        "id": 8,
        "input": "The Nova application uses Redis for caching.",
        "category": "duplicate",
        "expected": "DUPLICATE",
    },
    {
        "id": 9,
        "input": "The Orion API is developed using FastAPI.",
        "category": "duplicate",
        "expected": "DUPLICATE",
    },
    {
        "id": 10,
        "input": "React is used by the Phoenix frontend.",
        "category": "duplicate",
        "expected": "DUPLICATE",
    },

    # 3. Clear supersessions (5)
    {
        "id": 11,
        "input": "The Atlas project now uses MySQL instead of PostgreSQL.",
        "category": "supersession",
        "expected": "SUPERSEDE",
    },
    {
        "id": 12,
        "input": "The Nova application has switched from Redis to Memcached.",
        "category": "supersession",
        "expected": "SUPERSEDE",
    },
    {
        "id": 13,
        "input": "The Orion API now uses Django instead of FastAPI.",
        "category": "supersession",
        "expected": "SUPERSEDE",
    },
    {
        "id": 14,
        "input": "The Phoenix frontend has migrated from React to Vue.",
        "category": "supersession",
        "expected": "SUPERSEDE",
    },
    {
        "id": 15,
        "input": "The Mercury project now uses Qdrant instead of FAISS.",
        "category": "supersession",
        "expected": "SUPERSEDE",
    },

    # 4. Different contexts (5)
    {
        "id": 16,
        "input": "The production backend uses Python 3.12.",
        "category": "context",
        "expected": "ADD",
    },
    {
        "id": 17,
        "input": "The development backend uses Python 3.13.",
        "category": "context",
        "expected": "ADD",
    },
    {
        "id": 18,
        "input": "The testing backend uses Python 3.14.",
        "category": "context",
        "expected": "ADD",
    },
    {
        "id": 19,
        "input": "The production backend now uses Python 3.15.",
        "category": "context",
        "expected": "SUPERSEDE",
    },
    {
        "id": 20,
        "input": "The development backend now uses Python 3.14.",
        "category": "context",
        "expected": "SUPERSEDE",
    },

    # 5. Genuine conflicts (5)
    {
        "id": 21,
        "input": "The billing service uses Stripe for payments.",
        "category": "conflict",
        "expected": "ADD",
    },
    {
        "id": 22,
        "input": "The billing service uses Razorpay for payments.",
        "category": "conflict",
        "expected": "CONFLICT",
    },
    {
        "id": 23,
        "input": "The notification service uses SendGrid for email.",
        "category": "conflict",
        "expected": "ADD",
    },
    {
        "id": 24,
        "input": "The notification service uses Amazon SES for email.",
        "category": "conflict",
        "expected": "CONFLICT",
    },
    {
        "id": 25,
        "input": "The search service uses Elasticsearch for indexing.",
        "category": "conflict",
        "expected": "ADD",
    },

    # 6. Unrelated facts (5)
    {
        "id": 26,
        "input": "The mobile application supports dark mode.",
        "category": "unrelated",
        "expected": "ADD",
    },
    {
        "id": 27,
        "input": "The analytics service generates weekly reports.",
        "category": "unrelated",
        "expected": "ADD",
    },
    {
        "id": 28,
        "input": "The authentication service supports OAuth 2.0.",
        "category": "unrelated",
        "expected": "ADD",
    },
    {
        "id": 29,
        "input": "The documentation website uses Markdown.",
        "category": "unrelated",
        "expected": "ADD",
    },
    {
        "id": 30,
        "input": "The deployment pipeline runs automated tests.",
        "category": "unrelated",
        "expected": "ADD",
    },

    # 7. Temporal facts (5)
    {
        "id": 31,
        "input": "The analytics service started using Python 3.12 on October 10, 2026.",
        "category": "temporal",
        "expected": "ADD",
    },
    {
        "id": 32,
        "input": "The Orion API migrated to Django on October 20, 2026.",
        "category": "temporal",
        "expected": "SUPERSEDE",
    },
    {
        "id": 33,
        "input": "The Phoenix frontend migrated to Vue on November 1, 2026.",
        "category": "temporal",
        "expected": "SUPERSEDE",
    },
    {
        "id": 34,
        "input": "The Nova application stopped using Redis on October 15, 2026.",
        "category": "temporal",
        "expected": "ADD",
    },
    {
        "id": 35,
        "input": "The billing service adopted Stripe on September 1, 2026.",
        "category": "temporal",
        "expected": "ADD",
    },

    # 8. Ambiguous facts (5)
    {
        "id": 36,
        "input": "The backend might move to Go in the future.",
        "category": "ambiguous",
        "expected": "ADD",
    },
    {
        "id": 37,
        "input": "The database may be replaced with MongoDB.",
        "category": "ambiguous",
        "expected": "ADD",
    },
    {
        "id": 38,
        "input": "The team is considering switching to Kubernetes.",
        "category": "ambiguous",
        "expected": "ADD",
    },
    {
        "id": 39,
        "input": "The application could support multiple languages later.",
        "category": "ambiguous",
        "expected": "ADD",
    },
    {
        "id": 40,
        "input": "The search engine might eventually use a different vector database.",
        "category": "ambiguous",
        "expected": "ADD",
    },

    # 9. Multiple values that can coexist (5)
    {
        "id": 41,
        "input": "The application supports English.",
        "category": "coexist",
        "expected": "ADD",
    },
    {
        "id": 42,
        "input": "The application supports Hindi.",
        "category": "coexist",
        "expected": "COEXIST",
    },
    {
        "id": 43,
        "input": "The analytics service supports CSV exports.",
        "category": "coexist",
        "expected": "ADD",
    },
    {
        "id": 44,
        "input": "The analytics service supports JSON exports.",
        "category": "coexist",
        "expected": "COEXIST",
    },
    {
        "id": 45,
        "input": "The application supports both desktop and mobile platforms.",
        "category": "coexist",
        "expected": "ADD",
    },

    # 10. Mixed and additional cases (5)
    {
        "id": 46,
        "input": "The payment service uses Stripe for subscriptions.",
        "category": "mixed",
        "expected": "ADD",
    },
    {
        "id": 47,
        "input": "The payment service uses Razorpay for one-time payments.",
        "category": "mixed",
        "expected": "COEXIST",
    },
    {
        "id": 48,
        "input": "The production database uses PostgreSQL.",
        "category": "mixed",
        "expected": "ADD",
    },
    {
        "id": 49,
        "input": "The production database now uses MySQL.",
        "category": "mixed",
        "expected": "CONFLICT",
    },
    {
        "id": 50,
        "input": "The production database has been migrated from PostgreSQL to MySQL.",
        "category": "mixed",
        "expected": "SUPERSEDE",
    },
]
