app.post('/auth', async (req, res) => {
    const { key, hwid, version } = req.body;
    
    // Validate format before DB lookup
    if (!validKeyFormat(key))
        return res.json({ valid: false, reason: "INVALID_FORMAT" });
    
    // Rate limit by IP — stop brute force
    if (await isRateLimited(req.ip))
        return res.json({ valid: false, reason: "RATE_LIMITED" });
    
    const record = await db.keys.findOne({ key });
    
    if (!record)
        return res.json({ valid: false, reason: "NOT_FOUND" });
    
    if (record.banned)
        return res.json({ valid: false, reason: "BANNED", banReason: record.banReason });
    
    if (!record.active)
        return res.json({ valid: false, reason: "INACTIVE" });
    
    if (new Date() > record.expiresAt)
        return res.json({ valid: false, reason: "EXPIRED" });
    
    // HWID check
    if (record.hwid && record.hwid !== hwid)
        return res.json({ valid: false, reason: "HWID_MISMATCH" });
    
    // Version check — force updates
    if (version < MINIMUM_VERSION)
        return res.json({ valid: false, reason: "OUTDATED" });
    
    // Bind HWID on first auth
    if (!record.hwid) {
        await db.keys.updateOne({ key }, {
            $set:  { hwid },
            $inc:  { uses: 1 }
        });
    }
    
    // Sign and return token
    const token = jwt.sign(
        { key, hwid, tier: record.tier, expiresAt: record.expiresAt },
        process.env.JWT_SECRET,
        { expiresIn: '1h' } // short lived — reauth every hour
    );
    
    res.json({ valid: true, token, tier: record.tier });
});
