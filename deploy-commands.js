require('dotenv').config();
const { MongoClient } = require("mongodb");
const fs = require('fs');
const { SlashCommandBuilder } = require('@discordjs/builders');
const { REST } = require('@discordjs/rest');
const { Routes } = require('discord-api-types/v9');

const clientId = process.env.CLIENT_ID;
const guildId = process.env.GUILD_ID;
const token = process.env.DISCORD_TOKEN_JS;
const uri = process.env.MONGO_URL;

const mongo_client = new MongoClient(uri);

async function deploy_commands() {
	try {
		// console.log(!!mongo_client && !!mongo_client.topology && mongo_client.topology.isConnected());
		// get commands from "commands" folder
		const commands = fs.readdirSync('./commands').filter(file => file.endsWith('.js'))
			.map(file => require(`./commands/${file}`).data.toJSON());

		const rest = new REST({ version: '9' }).setToken(token);

		rest.put(Routes.applicationGuildCommands(clientId, guildId), { body: commands })
			.then(() => console.log('Successfully registered application commands.'))
			.catch(console.error);
	}
	catch (err) {
		console.error(err);
	}
	// finally {
	// 	mongo_client.close();
	// }
}

deploy_commands();
