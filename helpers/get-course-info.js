// helper to connect to (mongodb) database

const { MongoClient } = require("mongodb");
require('dotenv').config();

// import connect to db script
const run_db_query = require('./get-course-info');

// get course info
// if course does not exist, throw error
// if cannot get for current term, try again for the subsequent term
// if cannot get for any term, return "generic" response (so no term data)
/**
 * 
 * @param {*} subjectCode - subject code of course
 * @param {*} catalogNumber - catalog number of course
 * @param {*} season - season to query (Fall, Winter or Spring)
 * @param {*} fall 
 */
async function get_course_info(subjectCode, catalogNumber, season, year) {
    // try to see if the course exists first
    const course = await run_db_query('courses-descriptions', {
        subjectCode: subjectCode,
        catalogNumber: catalogNumber,
    });
    // if course is not found, throw error
    if (!course) throw Error('course not found');
}

console.log(get_course_info("MATH", "101", "2119"));
