// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "CodexCompanionDemo",
    platforms: [.macOS(.v14)],
    products: [.executable(name: "CompanionDemo", targets: ["CompanionDemo"])],
    targets: [
        .target(name: "CompanionCore"),
        .executableTarget(name: "CompanionDemo", dependencies: ["CompanionCore"]),
        .executableTarget(name: "CompanionCoreChecks", dependencies: ["CompanionCore"], path: "Checks")
    ]
)
