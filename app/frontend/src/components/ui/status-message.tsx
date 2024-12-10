import "./status-message.css";
import { useTranslation } from "react-i18next";

type Properties = {
    isRecording: boolean;
};

export default function StatusMessage({ isRecording }: Properties) {
    const { t } = useTranslation();
    if (!isRecording) {
        return <p className="text mb-4 mt-6">{t("status.notRecordingMessage")}</p>;
    }

    return (
        <div className="flex items-center">
            <div className="relative mt-8 h-36 w-36 overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-around">
                    {[...Array(4)].map((_, i) => (
                        <div
                            key={i}
                            className="w-2.5 rounded-full bg-blue-700 opacity-80"
                            style={{
                                animation: `barHeight${(i % 3) + 1} 1s ease-in-out infinite`,
                                animationDelay: `${i * 0.1}s`
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
