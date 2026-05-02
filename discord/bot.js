const { Client, GatewayIntentBits, EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const { MongoClient } = require('mongodb');
const crypto = require('crypto');

const bot = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages] });
const db = // your mongo connection

// ── Slash commands ──────────────────────────────────────

// /genkey tier:PRO days:30
// /resethjwid key:APB-PRO-XXXXXX
// /keyinfo key:APB-PRO-XXXXXX
// /ban key:APB-PRO-XXXXXX reason:sharing
// /unban key:APB-PRO-XXXXXX
// /extend key:APB-PRO-XXXXXX days:30
// /listkeys user:@someone
// /stats

bot.on('interactionCreate', async interaction => {
    if (!interaction.isChatInputCommand()) return;

    // Only allow in your server + admin role
    const ADMIN_ROLE = 'YOUR_ADMIN_ROLE_ID';
    if (!interaction.member.roles.cache.has(ADMIN_ROLE)) {
        return interaction.reply({ content: 'No permission.', ephemeral: true });
    }

    const { commandName } = interaction;

    // ── /genkey ─────────────────────────────────────────
    if (commandName === 'genkey') {
        const tier   = interaction.options.getString('tier');
        const days   = interaction.options.getInteger('days');
        const amount = interaction.options.getInteger('amount') ?? 1;

        const keys = [];
        for (let i = 0; i < amount; i++) {
            const key = generateKey(tier);
            await db.collection('keys').insertOne({
                key,
                tier,
                hwid:      null,
                createdAt: new Date(),
                expiresAt: new Date(Date.now() + days * 86400000),
                active:    true,
                banned:    false,
                hwidResets: 0,
                note:      '',
            });
            keys.push(key);
        }

        const embed = new EmbedBuilder()
            .setTitle('Keys Generated')
            .setColor(0x00FF00)
            .setDescription(keys.map(k => `\`${k}\``).join('\n'))
            .addFields(
                { name: 'Tier',    value: tier,           inline: true },
                { name: 'Days',    value: String(days),   inline: true },
                { name: 'Amount',  value: String(amount), inline: true },
            )
            .setTimestamp();

        // Send to admin only (ephemeral) so keys arent leaked in chat
        await interaction.reply({ embeds: [embed], ephemeral: true });

        // Log to your log channel
        logAction(interaction.client, 'KEY_GENERATED', {
            admin: interaction.user.tag,
            tier, days, amount, keys
        });
    }

    // ── /resethjwid ──────────────────────────────────────
    else if (commandName === 'resethwid') {
        const key = interaction.options.getString('key');
        const record = await db.collection('keys').findOne({ key });

        if (!record)
            return interaction.reply({ content: 'Key not found.', ephemeral: true });

        // Limit resets per month
        const resetCount = await db.collection('logs').countDocuments({
            action: 'HWID_RESET',
            key,
            timestamp: { $gte: startOfMonth() }
        });

        if (resetCount >= 2)
            return interaction.reply({ 
                content: `Reset limit reached (2/month). Last reset was ${record.lastReset?.toDateString()}.`,
                ephemeral: true 
            });

        await db.collection('keys').updateOne({ key }, {
            $set: { hwid: null, lastReset: new Date() },
            $inc: { hwidResets: 1 }
        });

        await db.collection('logs').insertOne({
            action:    'HWID_RESET',
            key,
            admin:     interaction.user.tag,
            timestamp: new Date()
        });

        await interaction.reply({
            embeds: [new EmbedBuilder()
                .setTitle('HWID Reset')
                .setColor(0xFFAA00)
                .addFields({ name: 'Key', value: `\`${key}\`` })
                .setTimestamp()
            ],
            ephemeral: true
        });
    }

    // ── /keyinfo ─────────────────────────────────────────
    else if (commandName === 'keyinfo') {
        const key = interaction.options.getString('key');
        const record = await db.collection('keys').findOne({ key });

        if (!record)
            return interaction.reply({ content: 'Key not found.', ephemeral: true });

        const expired = new Date() > record.expiresAt;
        const status  = record.banned ? '🔴 Banned'
                      : expired       ? '🟡 Expired'
                      : '🟢 Active';

        await interaction.reply({
            embeds: [new EmbedBuilder()
                .setTitle('Key Info')
                .setColor(record.banned ? 0xFF0000 : expired ? 0xFFAA00 : 0x00FF00)
                .addFields(
                    { name: 'Key',        value: `\`${key}\``,                          inline: false },
                    { name: 'Status',     value: status,                                inline: true  },
                    { name: 'Tier',       value: record.tier,                           inline: true  },
                    { name: 'HWID',       value: record.hwid ?? 'Not bound',            inline: false },
                    { name: 'Expires',    value: record.expiresAt.toDateString(),       inline: true  },
                    { name: 'Resets',     value: String(record.hwidResets),             inline: true  },
                    { name: 'Note',       value: record.note || 'None',                 inline: false },
                )
                .setTimestamp()
            ],
            ephemeral: true
        });
    }

    // ── /ban ─────────────────────────────────────────────
    else if (commandName === 'ban') {
        const key    = interaction.options.getString('key');
        const reason = interaction.options.getString('reason') ?? 'No reason given';

        await db.collection('keys').updateOne({ key }, {
            $set: { banned: true, banReason: reason }
        });

        await interaction.reply({
            embeds: [new EmbedBuilder()
                .setTitle('Key Banned')
                .setColor(0xFF0000)
                .addFields(
                    { name: 'Key',    value: `\`${key}\`` },
                    { name: 'Reason', value: reason       },
                )
                .setTimestamp()
            ]
        });

        logAction(interaction.client, 'BAN', { admin: interaction.user.tag, key, reason });
    }

    // ── /extend ──────────────────────────────────────────
    else if (commandName === 'extend') {
        const key  = interaction.options.getString('key');
        const days = interaction.options.getInteger('days');
        const record = await db.collection('keys').findOne({ key });

        if (!record)
            return interaction.reply({ content: 'Key not found.', ephemeral: true });

        // Extend from current expiry, not from today
        const newExpiry = new Date(record.expiresAt.getTime() + days * 86400000);

        await db.collection('keys').updateOne({ key }, {
            $set: { expiresAt: newExpiry }
        });

        await interaction.reply({
            embeds: [new EmbedBuilder()
                .setTitle('Key Extended')
                .setColor(0x00FF00)
                .addFields(
                    { name: 'Key',        value: `\`${key}\``          },
                    { name: 'New Expiry', value: newExpiry.toDateString() },
                )
                .setTimestamp()
            ],
            ephemeral: true
        });
    }

    // ── /stats ───────────────────────────────────────────
    else if (commandName === 'stats') {
        const total   = await db.collection('keys').countDocuments();
        const active  = await db.collection('keys').countDocuments({ banned: false, expiresAt: { $gt: new Date() } });
        const banned  = await db.collection('keys').countDocuments({ banned: true });
        const expired = await db.collection('keys').countDocuments({ expiresAt: { $lt: new Date() } });
        const unbound = await db.collection('keys').countDocuments({ hwid: null });

        await interaction.reply({
            embeds: [new EmbedBuilder()
                .setTitle('APBreaker Stats')
                .setColor(0x5865F2)
                .addFields(
                    { name: 'Total Keys', value: String(total),   inline: true },
                    { name: 'Active',     value: String(active),  inline: true },
                    { name: 'Banned',     value: String(banned),  inline: true },
                    { name: 'Expired',    value: String(expired), inline: true },
                    { name: 'Unbound',    value: String(unbound), inline: true },
                )
                .setTimestamp()
            ],
            ephemeral: true
        });
    }
});

// ── Helpers ─────────────────────────────────────────────

function generateKey(tier) {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const seg = (n) => Array.from({ length: n }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
    return `APB-${tier}-${seg(6)}-${seg(6)}-${seg(6)}`;
}

function startOfMonth() {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1);
}

async function logAction(client, action, data) {
    const LOG_CHANNEL = 'YOUR_LOG_CHANNEL_ID';
    const channel = await client.channels.fetch(LOG_CHANNEL);
    channel.send({
        embeds: [new EmbedBuilder()
            .setTitle(`Log — ${action}`)
            .setColor(0x5865F2)
            .setDescription(`\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``)
            .setTimestamp()
        ]
    });
}

bot.login('YOUR_BOT_TOKEN');
