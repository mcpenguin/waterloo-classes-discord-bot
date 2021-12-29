// example for bot embeds
// delete before deploying

const { SlashCommandBuilder } = require('@discordjs/builders');
const { MessageEmbed } = require('discord.js');

const exampleEmbed = new MessageEmbed()
	.setColor('#0099ff')
	.setTitle('Some title')
	.setURL('https://discord.js.org/')
	// .setAuthor({ name: 'Some name', iconURL: 'https://i.imgur.com/AfFp7pu.png', url: 'https://discord.js.org' })
    .setAuthor("Example")
	.setDescription('Some description here')
	.setThumbnail('https://i.imgur.com/AfFp7pu.png')
	.addFields(
		{ name: 'Regular field title', value: 'Some value here' },
		{ name: '\u200B', value: '\u200B' },
		{ name: 'Inline field title', value: 'Some value here', inline: true },
		{ name: 'Inline field title', value: 'Some value here', inline: true },
	);

module.exports = {
	data: new SlashCommandBuilder()
		.setName('example')
		.setDescription('Displays information about the bot'),
	async execute(interaction) {
        try {
		    await interaction.reply({
                embeds: [exampleEmbed]
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
