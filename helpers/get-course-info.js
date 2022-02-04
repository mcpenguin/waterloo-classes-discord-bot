// get course info

const {getTermcode, getPreviousTermcode} = require('./termcode');

// import connect to db script
// const run_db_query = require('./run-db-query').run_db_query;

const CourseNotFoundException = () => {
    this.name = 'CourseNotFoundException';
}

// get course info
// if course does not exist, throw error
// if cannot get for current term, try again for the subsequent term
// if cannot get for any term, return "generic" response (so no term data)
/**
 * @param {MongoClient} mongo_client - the mongo client
 * @param {string} subjectCode - subject code of course
 * @param {string} catalogNumber - catalog number of course
 * @param {(9) Fall | (1) Winter | (5) Spring } season - season to query 
 * @param {int} year - year to query
 */
async function get_course_info(mongo_client, subjectCode, catalogNumber, season, year) {
    const courses_descriptions = mongo_client.db('waterloo').collection('courses-descriptions');

    // try to see if the course exists first
    const defaultCourse = await courses_descriptions.findOne({
        subjectCode: subjectCode,
        catalogNumber: catalogNumber,
    });
    // if course is not found, throw CourseNotFoundException
    if (!defaultCourse) throw new CourseNotFoundException();
    
    // otherwise, if course is found, try to find it in the class schedule
    const courses = mongo_client.db('waterloo').collection('courses');
    // starting with the specified season and year
    let course = null;
    // get the termcode for the season and year
    let termcode = getTermcode(season, year);
    while (true) {
        // get the course from the class schedule
        course = await courses.findOne({
            subjectCode: subjectCode,
            catalogNumber: catalogNumber,
            term: termcode,
        });
        // if course is valid or termcode is < 1010, break
        if (course || parseInt(termcode) < 1010) break;
        // decrement termcode
        termcode = getPreviousTermcode(termcode);
    }
    // if course is valid return that aggregated with the "default" properties
    if (course) return {...course, ...defaultCourse};
    // otherwise return the "default" course
    return defaultCourse;
}

// get_course_info("MATH", "145", '5', '2021').then(console.log).catch(console.error);
// get_course_info("MATH", "147", '5', '2021').then(console.log).catch(console.error);

module.exports = {
    get_course_info,
}
