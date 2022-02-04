// run query on db js

const { MongoClient } = require("mongodb");
require('dotenv').config();

const uri = process.env.MONGO_URL;
const client = new MongoClient(uri);

/**
 * @description run query on db and return result (if any)
 * @param {string} collection - the collection to query
 * @param {string} query - the query to execute
 * @param {int} limit - number of results to return (default to be infinite)
 * @returns {list} result
 */
async function run_db_query(collection, query, limit=null) {
    try {
        const database = client.db('waterloo');
        const col = database.collection(collection);
        const result = 
            limit === 1 ? await col.findOne(query) :
            limit ? await col.find(query).limit(limit).toArray() :
            await col.find(query).toArray();
        return result;
    } 
    catch (err) {
        console.error(err);
    }
}


module.exports = {
    run_db_query
};
