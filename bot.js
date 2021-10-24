require('dotenv').config();

// const Discord = require('discord.js');
// const client = new Discord.Client({intents: ["DISCORD_GUILD"]});

// client.on('ready', () => {
//     console.log("Bot is ready");
// });

// client.login("OTAxOTA4MTQ4MTkxODk1NTgy.YXWtaw.NiJlIYHgoVSe2gGOfCNzolcKsrk");

// client.on('messageCreate', message => {
//     console.log(message.content);

//     if (message.content === 'ping') {
//         message.reply('pong');
//     }
// });

const { Client, Intents } = require('discord.js');
const client = new Client({ intents: [Intents.FLAGS.GUILDS] });

client.once('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.on('interactionCreate', async interaction => {
	if (!interaction.isCommand()) return;

	const { commandName } = interaction;

	if (commandName === 'ping') {
		await interaction.reply('Pong!');
	} else if (commandName === 'server') {
		await interaction.reply('Server info.');
	} else if (commandName === 'user') {
		await interaction.reply('User info.');
	}
});

client.login(process.env.DISCORD_TOKEN_JS);