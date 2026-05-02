// Discord bot command or dashboard
app.post('/admin/reset-hwid', adminAuth, async (req, res) => {
    const { key } = req.body;
    
    await db.keys.updateOne({ key }, {
        $set: { hwid: null },
        $inc: { hwidResets: 1 }
    });
    
    // Log the reset for abuse tracking
    await db.logs.insertOne({
        action: 'HWID_RESET',
        key,
        timestamp: new Date(),
        admin: req.admin
    });
    
    res.json({ success: true });
});

// Limit resets per month to prevent abuse
const resetThisMonth = await db.logs.countDocuments({
    action: 'HWID_RESET',
    key,
    timestamp: { $gte: startOfMonth }
});

if (resetThisMonth >= 2)
    return res.json({ success: false, reason: "Reset limit reached" });
