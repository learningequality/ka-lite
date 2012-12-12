require 'rubygems'
require 'open-uri'
require 'json'

maplayout = open("http://www.khanacademy.org/api/v1/topicversion/default/maplayout").read

File.open("../static/data/maplayout_data.json", 'w') do |f|
    f.write(maplayout)
end

exceptions = {
    "multiplication-division" => ["arithmetic_word_problems", "negative_number_word_problems"],
    "conic-sections" => ["parabola_intuition_3"]
}

JSON.parse(maplayout)["topics"].each do |k, v|
    topicdata = open("http://www.khanacademy.org/api/v1/topic/#{k}/exercises").read

    topic_exceptions = exceptions[k]

    if topic_exceptions != nil
        excepted = JSON.dump(JSON.parse(topicdata).map do |exercise|
            if topic_exceptions.include? exercise["name"]
                []
            else
                exercise
            end
        end.flatten)
    else
        excepted = topicdata
    end

    File.open("../static/data/topicdata/#{k}.json", 'w') do |f|
        f.write(excepted)
    end
end
