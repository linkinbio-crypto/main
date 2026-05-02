// Key schema
const keySchema = {
    key:       String,   // "APB-PRO-A3F9K2-..."
    tier:      String,   // "TRI" | "STD" | "PRO"
    hwid:      String,   // bound on first use, null until then
    createdAt: Date,
    expiresAt: Date,
    active:    Boolean,
    uses:      Number,   // how many times it's been used
    maxUses:   Number,   // 1 for personal, higher for resellers
    note:      String,   // e.g. "Discord: username#1234"
    banned:    Boolean,
    banReason: String,
}

// Key generation endpoint (admin only)
app.post('/admin/generate', adminAuth, async (req, res) => {
    const { tier, days, amount, maxUses } = req.body;
    
    const keys = [];
    for (let i = 0; i < amount; i++) {
        const key = generateKey(tier);
        await db.keys.insertOne({
            key,
            tier,
            hwid:      null,
            createdAt: new Date(),
            expiresAt: new Date(Date.now() + days * 86400000),
            active:    true,
            uses:      0,
            maxUses:   maxUses || 1,
            banned:    false,
        });
        keys.push(key);
    }
    res.json({ keys });
});
