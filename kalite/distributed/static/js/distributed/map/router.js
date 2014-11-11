MapChannelRouter = ChannelRouter.extend({
    navigate_channel: function(channel, splat) {
        if (this.channel!==channel) {
            this.control_view = new KnowledgeMapView({
                el: "#map-container"
            });
            this.channel = channel;
        }
        this.navigate_splat(splat);
    }
});