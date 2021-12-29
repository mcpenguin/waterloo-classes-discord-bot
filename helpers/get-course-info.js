// get course info

const {getTermcode, getPreviousTermcode} = require('./termcode');

// import connect to db script
const run_db_query = require('./run-db-query').run_db_query;

const CourseNotFoundException = () => {
    this.name = 'CourseNotFoundException';
}

// get course info
// if course does not exist, throw error
// if cannot get for current term, try again for the subsequent term
// if cannot get for any term, return "generic" response (so no term data)
/**
 * 
 * @param {string} subjectCode - subject code of course
 * @param {string} catalogNumber - catalog number of course
 * @param {Fall | Winter | Spring } season - season to query (Fall, Winter or Spring)
 * @param {int} year - year to query
 */
async function get_course_info(subjectCode, catalogNumber, season, year) {
    // try to see if the course exists first
    const defaultCourse = await run_db_query('courses-descriptions', {
        subjectCode: subjectCode,
        catalogNumber: catalogNumber,
    }, 1);
    // if course is not found, throw CourseNotFoundException
    if (!defaultCourse) throw new CourseNotFoundException();
    
    // otherwise, if course is found, try to find it in the class schedule
    // starting with the specified season and year
    let course = null;
    // get the termcode for the season and year
    let termcode = getTermcode(season, year);
    while (true) {
        // get the termcode for the season and year
        console.log(termcode);
        // get the course from the class schedule
        course = await run_db_query('courses', {
            subjectCode: subjectCode,
            catalogNumber: catalogNumber,
            term: termcode,
        }, 1);
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

get_course_info("MATH", "145", '5', '2021').then(console.log).catch(console.error);
