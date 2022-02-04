require('dotenv').config();

const { MongoClient } = require("mongodb");
const {db_connect, db_close} = require('./helpers/run-db-query');

const fs = require('fs');
const { Client, Collection, Intents } = require('discord.js');

const client = new Client({ intents: [Intents.FLAGS.GUILDS] });

const uri = process.env.MONGO_URL;
const mongo_client = new MongoClient(uri);

client.commands = new Collection();

// build collection of commands
const commandFiles = fs.readdirSync('./commands').filter(file => file.endsWith('.js'));

for (const file of commandFiles) {
    const command = require(`./commands/${file}`);
    // Set a new item in the Collection
    // With the key as the command name and the value as the exported module
    client.commands.set(command.data.name, command);
}

client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});

client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    await mongo_client.connect();
    const command = client.commands.get(interaction.commandName);
    try {
        await command.execute(interaction, mongo_client);
    }
    catch (err) {
        console.error(err);
        await interaction.reply({
            content: `There was an error executing the command: ${interaction.commandName}`,
            ephemeral: true,
        });
    }
});

async function main() {
    try {
        await mongo_client.connect();
        client.login(process.env.DISCORD_TOKEN_JS);
    }
    catch (err) {
        console.error(err);
    }
    // finally {
    //     console.log("end");
    //     mongo_client.close();
    // };
}

main();

