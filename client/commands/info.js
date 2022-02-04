// get info about discord bot
const { SlashCommandBuilder } = require('@discordjs/builders');
const { MessageEmbed } = require('discord.js');

const embed = interaction => {
	// console.log(interaction.options.get('test').value);
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
		.setName('info')
		.setDescription('Displays information about the bot')
		.addStringOption(option => option
			.setName('test')
			.setDescription('the test category')
			.setRequired(true)
		)
		,
	async execute(interaction, mongo_client) {
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
