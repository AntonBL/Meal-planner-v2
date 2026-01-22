# SwiftUI Frontend Guide

**Building the Plant Tracker iOS App with SwiftUI**

---

## Table of Contents

1. [Project Setup](#project-setup)
2. [App Architecture (MVVM)](#app-architecture-mvvm)
3. [Data Models](#data-models)
4. [Networking Layer](#networking-layer)
5. [Local Storage (SwiftData)](#local-storage-swiftdata)
6. [Camera & Photo Library](#camera--photo-library)
7. [Notifications](#notifications)
8. [Key SwiftUI Patterns](#key-swiftui-patterns)
9. [Keychain for Tokens](#keychain-for-tokens)

---

## Project Setup

### Create New Xcode Project

1. Open Xcode
2. Create new iOS App
3. Choose SwiftUI interface
4. Enable CloudKit (optional, for iCloud sync later)

### Project Structure

```
PlantTracker/
├── PlantTrackerApp.swift        # App entry point
├── Models/                      # Data models
│   ├── Plant.swift
│   ├── WateringEvent.swift
│   └── HealthReport.swift
│
├── Views/                       # UI views
│   ├── PlantListView.swift
│   ├── PlantDetailView.swift
│   ├── AddPlantView.swift
│   ├── WateringHistoryView.swift
│   └── Components/
│       ├── PlantCardView.swift
│       └── WateringButtonView.swift
│
├── ViewModels/                  # View models (MVVM)
│   ├── PlantListViewModel.swift
│   ├── PlantDetailViewModel.swift
│   └── AddPlantViewModel.swift
│
├── Services/                    # Business logic
│   ├── APIClient.swift          # Network layer
│   ├── PlantService.swift
│   ├── NotificationService.swift
│   └── ImageService.swift
│
├── Storage/                     # Local data
│   ├── PlantStore.swift         # SwiftData store
│   └── KeychainHelper.swift     # Keychain wrapper
│
└── Utilities/
    ├── Constants.swift
    └── Extensions/
        ├── Date+Extensions.swift
        └── View+Extensions.swift
```

---

## App Architecture (MVVM)

### Why MVVM?

**Model-View-ViewModel pattern separates:**
- **Model**: Data structures (Plant, WateringEvent)
- **View**: SwiftUI views (UI only, no business logic)
- **ViewModel**: Business logic, state management, API calls

**Benefits:**
- Testable (test ViewModels without UI)
- Clean separation of concerns
- Reactive updates with `@Published` properties

### App Entry Point (PlantTrackerApp.swift)

```swift
import SwiftUI
import SwiftData

@main
struct PlantTrackerApp: App {
    // SwiftData model container
    let modelContainer: ModelContainer

    init() {
        do {
            // Initialize SwiftData for local storage
            modelContainer = try ModelContainer(for: Plant.self, WateringEvent.self)
        } catch {
            fatalError("Could not initialize ModelContainer: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(modelContainer)
    }
}
```

---

## Data Models

### Plant Model (Models/Plant.swift)

```swift
import Foundation
import SwiftData

@Model
final class Plant {
    @Attribute(.unique) var id: String
    var name: String
    var species: String?
    var wateringFrequencyDays: Int
    var lastWatered: Date?
    var healthStatus: String
    var notes: String?
    var createdAt: Date

    // Computed property
    var needsWatering: Bool {
        guard let lastWatered = lastWatered else {
            return true // Never watered
        }

        let daysSinceWatered = Calendar.current.dateComponents(
            [.day],
            from: lastWatered,
            to: Date()
        ).day ?? 0

        return daysSinceWatered >= wateringFrequencyDays
    }

    var nextWateringDate: Date? {
        guard let lastWatered = lastWatered else {
            return nil
        }
        return Calendar.current.date(
            byAdding: .day,
            value: wateringFrequencyDays,
            to: lastWatered
        )
    }

    init(
        id: String = UUID().uuidString,
        name: String,
        species: String? = nil,
        wateringFrequencyDays: Int,
        lastWatered: Date? = nil,
        healthStatus: String = "unknown",
        notes: String? = nil,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.species = species
        self.wateringFrequencyDays = wateringFrequencyDays
        self.lastWatered = lastWatered
        self.healthStatus = healthStatus
        self.notes = notes
        self.createdAt = createdAt
    }
}
```

### Codable Models for API (Models/PlantDTO.swift)

```swift
import Foundation

// Data Transfer Object for API communication
struct PlantDTO: Codable {
    let id: String?
    let name: String
    let species: String?
    let wateringFrequencyDays: Int
    let lastWatered: Date?
    let healthStatus: String?
    let notes: String?
    let createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case species
        case wateringFrequencyDays = "watering_frequency_days"
        case lastWatered = "last_watered"
        case healthStatus = "health_status"
        case notes
        case createdAt = "created_at"
    }
}

// Convert between Plant and PlantDTO
extension Plant {
    func toDTO() -> PlantDTO {
        PlantDTO(
            id: id,
            name: name,
            species: species,
            wateringFrequencyDays: wateringFrequencyDays,
            lastWatered: lastWatered,
            healthStatus: healthStatus,
            notes: notes,
            createdAt: createdAt
        )
    }

    static func from(dto: PlantDTO) -> Plant {
        Plant(
            id: dto.id ?? UUID().uuidString,
            name: dto.name,
            species: dto.species,
            wateringFrequencyDays: dto.wateringFrequencyDays,
            lastWatered: dto.lastWatered,
            healthStatus: dto.healthStatus ?? "unknown",
            notes: dto.notes,
            createdAt: dto.createdAt ?? Date()
        )
    }
}
```

---

## Networking Layer

### API Client (Services/APIClient.swift)

```swift
import Foundation

enum APIError: Error {
    case invalidURL
    case networkError(Error)
    case invalidResponse
    case decodingError(Error)
    case serverError(Int)
    case unauthorized

    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid response from server"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .serverError(let code):
            return "Server error: \(code)"
        case .unauthorized:
            return "Unauthorized - please log in"
        }
    }
}

class APIClient {
    static let shared = APIClient()

    private let baseURL = "http://localhost:8000/api"  // Change for production
    private let session: URLSession

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        session = URLSession(configuration: config)
    }

    // Generic request method
    func request<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Encodable? = nil,
        requiresAuth: Bool = true
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Add auth token if required
        if requiresAuth, let token = KeychainHelper.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Add body if present
        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }

        // Perform request
        let (data, response) = try await session.data(for: request)

        // Check response
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200...299:
            // Success - decode response
            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }

        case 401:
            throw APIError.unauthorized

        default:
            throw APIError.serverError(httpResponse.statusCode)
        }
    }

    // Upload image
    func uploadImage(
        endpoint: String,
        image: Data,
        parameters: [String: String] = [:]
    ) async throws -> Data {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        // Create multipart form data
        let boundary = UUID().uuidString
        request.setValue(
            "multipart/form-data; boundary=\(boundary)",
            forHTTPHeaderField: "Content-Type"
        )

        // Add auth token
        if let token = KeychainHelper.shared.getToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Build multipart body
        var body = Data()

        // Add parameters
        for (key, value) in parameters {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        // Add image
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(image)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.invalidResponse
        }

        return data
    }
}
```

### Plant Service (Services/PlantService.swift)

```swift
import Foundation

class PlantService {
    private let apiClient = APIClient.shared

    // Get all plants
    func getAllPlants() async throws -> [PlantDTO] {
        try await apiClient.request(endpoint: "/plants")
    }

    // Get single plant
    func getPlant(id: String) async throws -> PlantDTO {
        try await apiClient.request(endpoint: "/plants/\(id)")
    }

    // Create plant
    func createPlant(_ plant: PlantDTO) async throws -> PlantDTO {
        try await apiClient.request(
            endpoint: "/plants",
            method: "POST",
            body: plant
        )
    }

    // Update plant
    func updatePlant(_ plant: PlantDTO) async throws -> PlantDTO {
        try await apiClient.request(
            endpoint: "/plants/\(plant.id ?? "")",
            method: "PUT",
            body: plant
        )
    }

    // Delete plant
    func deletePlant(id: String) async throws {
        let _: EmptyResponse = try await apiClient.request(
            endpoint: "/plants/\(id)",
            method: "DELETE"
        )
    }

    // Record watering
    func recordWatering(plantId: String, wateredAt: Date) async throws {
        struct WateringRequest: Codable {
            let plantId: String
            let wateredAt: Date

            enum CodingKeys: String, CodingKey {
                case plantId = "plant_id"
                case wateredAt = "watered_at"
            }
        }

        let request = WateringRequest(plantId: plantId, wateredAt: wateredAt)
        let _: EmptyResponse = try await apiClient.request(
            endpoint: "/watering",
            method: "POST",
            body: request
        )
    }
}

// Empty response for endpoints that return nothing
struct EmptyResponse: Codable {}
```

---

## Local Storage (SwiftData)

### Plant Store (Storage/PlantStore.swift)

```swift
import SwiftUI
import SwiftData

@MainActor
class PlantStore: ObservableObject {
    private var modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    // Fetch all plants
    func fetchPlants() -> [Plant] {
        let descriptor = FetchDescriptor<Plant>(
            sortBy: [SortDescriptor(\.name)]
        )

        do {
            return try modelContext.fetch(descriptor)
        } catch {
            print("Failed to fetch plants: \(error)")
            return []
        }
    }

    // Fetch plants needing water
    func fetchPlantsNeedingWater() -> [Plant] {
        fetchPlants().filter { $0.needsWatering }
    }

    // Add plant
    func addPlant(_ plant: Plant) {
        modelContext.insert(plant)
        save()
    }

    // Update plant
    func updatePlant(_ plant: Plant) {
        // Plant is already tracked by SwiftData
        save()
    }

    // Delete plant
    func deletePlant(_ plant: Plant) {
        modelContext.delete(plant)
        save()
    }

    // Save context
    private func save() {
        do {
            try modelContext.save()
        } catch {
            print("Failed to save context: \(error)")
        }
    }
}
```

---

## Camera & Photo Library

### Image Picker (Utilities/ImagePicker.swift)

```swift
import SwiftUI
import PhotosUI

struct ImagePicker: UIViewControllerRepresentable {
    @Binding var image: UIImage?
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.filter = .images
        config.selectionLimit = 1

        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: ImagePicker

        init(_ parent: ImagePicker) {
            self.parent = parent
        }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.dismiss()

            guard let provider = results.first?.itemProvider else { return }

            if provider.canLoadObject(ofClass: UIImage.self) {
                provider.loadObject(ofClass: UIImage.self) { image, error in
                    DispatchQueue.main.async {
                        self.parent.image = image as? UIImage
                    }
                }
            }
        }
    }
}

// Usage in View
struct AddPlantView: View {
    @State private var selectedImage: UIImage?
    @State private var showImagePicker = false

    var body: some View {
        VStack {
            if let image = selectedImage {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(height: 200)
            }

            Button("Select Photo") {
                showImagePicker = true
            }
            .sheet(isPresented: $showImagePicker) {
                ImagePicker(image: $selectedImage)
            }
        }
    }
}
```

---

## Notifications

### Local Notifications (Services/NotificationService.swift)

```swift
import Foundation
import UserNotifications

class NotificationService {
    static let shared = NotificationService()

    private init() {}

    // Request notification permission
    func requestAuthorization() async -> Bool {
        do {
            return try await UNUserNotificationCenter.current()
                .requestAuthorization(options: [.alert, .sound, .badge])
        } catch {
            print("Failed to request notification authorization: \(error)")
            return false
        }
    }

    // Schedule watering reminder
    func scheduleWateringReminder(for plant: Plant) {
        guard let nextWateringDate = plant.nextWateringDate else {
            return
        }

        let content = UNMutableNotificationContent()
        content.title = "Time to Water!"
        content.body = "Don't forget to water your \(plant.name)"
        content.sound = .default

        // Calculate time interval
        let timeInterval = nextWateringDate.timeIntervalSinceNow

        guard timeInterval > 0 else {
            return // Date is in the past
        }

        let trigger = UNTimeIntervalNotificationTrigger(
            timeInterval: timeInterval,
            repeats: false
        )

        let request = UNNotificationRequest(
            identifier: "watering-\(plant.id)",
            content: content,
            trigger: trigger
        )

        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Failed to schedule notification: \(error)")
            }
        }
    }

    // Cancel watering reminder
    func cancelWateringReminder(for plantId: String) {
        UNUserNotificationCenter.current()
            .removePendingNotificationRequests(withIdentifiers: ["watering-\(plantId)"])
    }

    // Cancel all notifications
    func cancelAllNotifications() {
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
    }
}
```

---

## Key SwiftUI Patterns

### MVVM ViewModel Pattern

```swift
import Foundation
import Combine

@MainActor
class PlantListViewModel: ObservableObject {
    @Published var plants: [Plant] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let plantService = PlantService()
    private let plantStore: PlantStore

    init(plantStore: PlantStore) {
        self.plantStore = plantStore
        loadPlants()
    }

    // Load plants (offline-first: load from local, then sync with API)
    func loadPlants() {
        // Load from local storage immediately
        plants = plantStore.fetchPlants()

        // Then sync with API in background
        Task {
            await syncWithAPI()
        }
    }

    // Sync with API
    private func syncWithAPI() async {
        isLoading = true
        errorMessage = nil

        do {
            let plantDTOs = try await plantService.getAllPlants()

            // Update local storage
            for dto in plantDTOs {
                let plant = Plant.from(dto: dto)
                plantStore.addPlant(plant)
            }

            // Refresh list
            plants = plantStore.fetchPlants()

        } catch {
            errorMessage = error.localizedDescription
            print("Failed to sync plants: \(error)")
        }

        isLoading = false
    }

    // Add plant
    func addPlant(name: String, wateringFrequency: Int) async {
        let plant = Plant(
            name: name,
            wateringFrequencyDays: wateringFrequency
        )

        // Save locally first (optimistic update)
        plantStore.addPlant(plant)
        plants = plantStore.fetchPlants()

        // Then sync with API
        do {
            let dto = plant.toDTO()
            _ = try await plantService.createPlant(dto)
        } catch {
            errorMessage = "Failed to sync plant with server"
            print("Failed to create plant on server: \(error)")
        }
    }

    // Record watering
    func recordWatering(for plant: Plant) async {
        plant.lastWatered = Date()
        plantStore.updatePlant(plant)
        plants = plantStore.fetchPlants()

        // Schedule next reminder
        NotificationService.shared.scheduleWateringReminder(for: plant)

        // Sync with API
        do {
            try await plantService.recordWatering(
                plantId: plant.id,
                wateredAt: Date()
            )
        } catch {
            print("Failed to sync watering with server: \(error)")
        }
    }
}
```

### View Using ViewModel

```swift
import SwiftUI
import SwiftData

struct PlantListView: View {
    @StateObject private var viewModel: PlantListViewModel
    @State private var showAddPlant = false

    init(modelContext: ModelContext) {
        let store = PlantStore(modelContext: modelContext)
        _viewModel = StateObject(wrappedValue: PlantListViewModel(plantStore: store))
    }

    var body: some View {
        NavigationStack {
            List {
                ForEach(viewModel.plants) { plant in
                    PlantRow(plant: plant, viewModel: viewModel)
                }
            }
            .navigationTitle("My Plants")
            .toolbar {
                Button {
                    showAddPlant = true
                } label: {
                    Image(systemName: "plus")
                }
            }
            .sheet(isPresented: $showAddPlant) {
                AddPlantView(viewModel: viewModel)
            }
            .overlay {
                if viewModel.isLoading {
                    ProgressView()
                }
            }
        }
    }
}

struct PlantRow: View {
    let plant: Plant
    let viewModel: PlantListViewModel

    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(plant.name)
                    .font(.headline)

                if let nextWatering = plant.nextWateringDate {
                    Text("Next watering: \(nextWatering, style: .date)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            if plant.needsWatering {
                Button {
                    Task {
                        await viewModel.recordWatering(for: plant)
                    }
                } label: {
                    Image(systemName: "drop.fill")
                        .foregroundColor(.blue)
                }
            }
        }
    }
}
```

---

## Keychain for Tokens

### Keychain Helper (Storage/KeychainHelper.swift)

```swift
import Foundation
import Security

class KeychainHelper {
    static let shared = KeychainHelper()

    private let service = "com.yourapp.planttracker"

    private init() {}

    // Save token
    func saveToken(_ token: String) {
        let data = Data(token.utf8)

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: "authToken",
            kSecValueData as String: data
        ]

        // Delete existing
        SecItemDelete(query as CFDictionary)

        // Add new
        let status = SecItemAdd(query as CFDictionary, nil)

        if status != errSecSuccess {
            print("Failed to save token to keychain: \(status)")
        }
    }

    // Get token
    func getToken() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: "authToken",
            kSecReturnData as String: true
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }

        return token
    }

    // Delete token
    func deleteToken() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: "authToken"
        ]

        SecItemDelete(query as CFDictionary)
    }
}
```

---

## Next Steps

1. Review `05-claude-collaboration.md` for working with Claude Code
2. Check `06-quick-reference.md` for command cheatsheet
3. Start building your Plant Tracker app!
