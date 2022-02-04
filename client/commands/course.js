// get information about a course

const { SlashCommandBuilder } = require('@discordjs/builders');
const { MessageEmbed } = require('discord.js');

const color_config = require('../../color_config.json')
const get_course_info = require('../../helpers/get-course-info').get_course_info;
const get_subject_codes = require('../../helpers/get-subject-codes');

const getCurrentSeason = () => '1';
const getCurrentYear = () => '2022';

const embed = (interaction, mongo_client) => {

    // get fields
	let subjectCode = interaction.options.get('subjectCode').value;
    let catalogNumber = interaction.options.get('catalogNumber').value;
    let season = (s = interaction.options.get('season')) ? s.value : getCurrentSeason()
    let year = (y = interaction.options.get('year')) ? y.value : getCurrentYear();

	return new MessageEmbed()
		.setColor('#ffffff')
		.setTitle('Waterloo Classes Bot')
		.setURL('https://github.com/mcpenguin/waterloo-classes-discord-bot')
		.setAuthor('Marcus Chan', 'https://avatars.githubusercontent.com/mcpenguin', 'https://github.com/mcpenguin')
		.setDescription("*Waterloo Classes Bot* is a bot that allows you to search for classes offered by the University of Waterloo, using the UWaterloo Open Data API and a web scraper for classes.uwaterloo.ca.")
		.addFields(
			{ 
				name: 'Add the bot to other servers!', 
				value: 'https://discord.com/api/oauth2/authorize?client_id=877440425718333460&permissions=2048&scope=bot' 
			},
	);
}
module.exports = {
	data: new SlashCommandBuilder()
            .setName('course')
            .setDescription('Get information about a course')
            .addStringOption(option => option
                .setName('season')
                .setDescription('The season to query')
                // numbers correspond to the "termcode" that each season
                // correspond to
                .addChoice('Fall', '9')
                .addChoice('Winter', '1')
                .addChoice('Spring', '5')    
            )
            .addIntegerOption(option => option
                .setName('year')
                .setDescription('The year to query')
            ),
	async execute(interaction, mongo_client) {
        try {
            get_subject_codes(mongo_client).then(console.log);
		    await interaction.reply({
                embeds: [embed(interaction, mongo_client)]
            });
        } catch (err) {
            console.error(err);
            await interaction.reply({
                content: `There was an error executing the command: ${interaction.commandName}`,
                ephemeral: true,
            });
        }
	},
};
