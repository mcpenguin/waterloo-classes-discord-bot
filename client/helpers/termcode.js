// get termcode

/**
 * @description Convert season, year pair to termcode
 * @param {fall | winter | spring} season
 * @param {int} year
 * @returns {string} termcode
 */
function getTermcode(season, year) {
    return (year - 1900).toString() + season.toString();
}

/**
 * @description Get "previous" termcode
 * @param {string} termcode
 * @returns {string} newTermcode
 */
function getPreviousTermcode(termcode) {
    return parseInt(parseInt(termcode, 12) - 4, 10).toString(12);
}

module.exports = {
    getTermcode,
    getPreviousTermcode,
}
