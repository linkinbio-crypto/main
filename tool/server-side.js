// Node.js + Express + MongoDB
const express = require('express');
const crypto = require('crypto');
const app = express();

app.post('/auth', async (req, res) => {
    const { key, hwid } = req.body;
    
    const user = await db.keys.findOne({ key });
    
    if (!user)                          return res.json({ valid: false, reason: "Invalid key" });
    if (user.hwid && user.hwid !== hwid) return res.json({ valid: false, reason: "HWID mismatch" });
    if (user.expiry < Date.now())        return res.json({ valid: false, reason: "Expired" });
    
    // Bind HWID on first login
    if (!user.hwid) await db.keys.updateOne({ key }, { $set: { hwid } });
    
    // Sign a token so client can verify without hitting server every frame
    const token = signToken({ key, hwid, expiry: user.expiry });
    res.json({ valid: true, token });
});
