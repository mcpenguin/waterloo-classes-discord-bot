const run_db_query = require('./run-db-query').run_db_query;

/**
 * @description get list of subject codes
 * @param {MongoClient} mongo_client - the mongo client
 * @returns {list} subject codes
 * 
*/
async function getSubjectCodes(mongo_client) {
    const courses = mongo_client.db('waterloo').collection('courses');
    const subjectCodes = await courses.distinct('subjectCode');
    // remove numeric values
    return subjectCodes.filter(value => 
        isNaN(value) || (parseFloat(value) | 0) !== parseFloat(value)
    );
}

module.exports = getSubjectCodes;
