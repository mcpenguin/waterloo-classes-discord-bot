// get information about a course

const { SlashCommandBuilder } = require('@discordjs/builders');
const { MessageEmbed } = require('discord.js');

const getCurrentSeason = () => '1';
const getCurrentYear = () => '2022';

const embed = interaction => {
    // get fields
	let course = interaction.options.get('course').value;
    let season = interaction.options.get('season').value || getCurrentSeason();
    let year = interaction.options.get('year').value || getCurrentYear();

	return new MessageEmbed()
		.setColor('#0099ff')
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
            .setName('course')
            .setDescription('The course to get information about')
            .setRequired(true)
        )
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
        )
    ,
	async execute(interaction) {
        try {
		    await interaction.reply({
                embeds: [embed(interaction)]
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
