// =============================================================================
// MongoDB Initialization Script
// Creates database, collections, and indexes for RPA FluxLaw
// =============================================================================

// Switch to the application database
db = db.getSiblingDB('projeto_fluxlaw');

// Create collections
db.createCollection('tasks');

// Create indexes for better query performance
db.tasks.createIndex({ "process_number": 1 }, { unique: false });
db.tasks.createIndex({ "status": 1 });
db.tasks.createIndex({ "client_name": 1 });
db.tasks.createIndex({ "created_at": -1 });
db.tasks.createIndex({ "updated_at": -1 });

// Compound index for common queries
db.tasks.createIndex({ "status": 1, "client_name": 1, "created_at": -1 });

print('MongoDB initialized successfully for RPA FluxLaw');
print('Collections created: tasks');
print('Indexes created for optimal query performance');
